import os
import re
import time
from typing import Dict, Optional, List, Set, Union
from collections import deque

import json
import html2text
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel
from yaspin import yaspin


from .constants import DEFAULT_USER_AGENT, TAG_TO_REMOVE, FORMAT_TYPE
from urllib.parse import urlparse, urljoin


class Paw:
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        delay: float = 0.5,
        ignore_links: bool = True,
        ignore_images: bool = True,
        ignore_emphasis: bool = True,
        ignore_tables: bool = True,
        ignore_mailto_links: bool = True,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the Paw class.

        Args:
            headers: Optional headers to be used in HTTP requests.
            delay: Delay in seconds between requests.
            ignore_links: Whether to ignore links.
            ignore_images: Whether to ignore images.
            ignore_emphasis: Whether to ignore emphasis.
            ignore_tables: Whether to ignore tables.
            ignore_mailto_links: Whether to ignore mailto links.
        """
        self.headers = headers or {"User-Agent": DEFAULT_USER_AGENT}
        self.delay = delay
        self._converter = html2text.HTML2Text()
        self._converter.ignore_links = ignore_links
        self._converter.ignore_images = ignore_images
        self._converter.ignore_emphasis = ignore_emphasis
        self._converter.ignore_tables = ignore_tables
        self._converter.ignore_mailto_links = ignore_mailto_links

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract all links from a BeautifulSoup object.

        Args:
            soup: The BeautifulSoup object.
            base_url: The base URL to resolve relative URLs.

        Returns:
            A list of absolute URLs.
        """
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]

            # Skip empty href or link to fragment
            if not href or href.startswith("#"):
                continue

            # Convert relative URL to absolute URL
            absolute_url = urljoin(base_url, href)

            # Skip URLs with fragments or query parameters
            absolute_url = absolute_url.split("#")[0].split("?")[0]

            # Ensure the URL stays within the same domain
            if self._same_domain(absolute_url, base_url):
                links.append(absolute_url)

        return links

    def _same_domain(self, url: str, base_url: str) -> bool:
        """
        Check if a URL belongs to the same domain as the base URL.

        Args:
            url: The URL to check.
            base_url: The base URL to compare against.

        Returns:
            True if the URL belongs to the same domain, False otherwise.
        """
        url_domain = urlparse(url).netloc
        base_domain = urlparse(base_url).netloc

        # Remove 'www.' prefix for comparison
        url_domain = url_domain.replace("www.", "")
        base_domain = base_domain.replace("www.", "")

        return url_domain == base_domain

    def _clean_markdown(self, markdown: str) -> str:
        """
        Clean up the markdown by removing extra whitespace and line breaks.

        Args:
            markdown: The markdown to clean.

        Returns:
            The cleaned markdown.
        """
        # Remove multiple consecutive empty lines
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)

        # Remove trailing whitespaces
        markdown = re.sub(r" +\n", "\n", markdown)

        return markdown.strip()

    def scrape(self, url: str) -> str:
        """
        Scrape a webpage and return its content in markdown.

        Args:
            url: The URL of the webpage to scrape.

        Returns:
            The scraped content in the specified format.
        """
        try:
            # Validate URL
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {url}")

            # Fetch webpage content
            response: requests.Response = requests.get(
                url=url,
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()  # Raise exception for HTTP errors

            # Check if content is HTML
            content_type: str = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                raise ValueError(f"URL does not contain HTML content: {url}")

            # Parse HTML with BeautifulSoup
            soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")

            # Remove unnecessary tags for markdown conversion
            for tag in soup(TAG_TO_REMOVE):
                tag.decompose()

            # Convert to markdown
            markdown: str = self._converter.handle(str(soup))

            # Clean up the markdown
            markdown = self._clean_markdown(markdown)
            return markdown

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Error fetching URL {url}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing {url}: {str(e)}")

    def crawl(
        self,
        base_url: str,
        max_depth: int = 2,
        format_type: FORMAT_TYPE = "markdown",
    ) -> Union[str, Dict[str, str]]:
        """
        Crawl webpages starting from a base URL up to a specified depth.

        Args:
            base_url: The starting URL for crawling.
            max_depth: The maximum depth to crawl. Defaults to 2.
            format_type: The format to return ('markdown' or 'json').

        Returns:
            A dictionary with URLs as keys and their content (markdown or dict) as values.
        """
        # Validate base URL
        if not base_url.startswith(("http://", "https://")):
            raise ValueError(f"Invalid URL: {base_url}")

        # Queue to manage URLs to be visited (URL, depth)
        queue: deque = deque([(base_url, 0)])

        # Set to track visited URLs
        visited: Set[str] = set()

        # Dictionary to store content
        content_dict: Dict[str, str] = {}

        while queue:
            url, depth = queue.popleft()

            # Skip if URL already visited or depth exceeds max_depth
            if url in visited or depth > max_depth:
                continue

            try:
                with yaspin(
                    text=f"Crawling: {url} (Depth: {depth})"
                ) as spinner:
                    # Mark URL as visited
                    visited.add(url)

                    # Fetch and parse webpage
                    response = requests.get(
                        url, headers=self.headers, timeout=10
                    )
                    response.raise_for_status()

                    # Check if content is HTML
                    content_type = response.headers.get("Content-Type", "")
                    if "text/html" not in content_type:
                        continue

                    # Parse HTML
                    soup = BeautifulSoup(response.text, "html.parser")

                    # Convert to markdown/json and store
                    content_dict[url] = self.scrape(url)

                    # Extract links for the next level if not at max depth
                    if depth < max_depth:
                        links = self._extract_links(soup, url)
                        for link in links:
                            if link not in visited:
                                queue.append((link, depth + 1))

                    # Respect the website by adding a delay between requests
                    time.sleep(self.delay)

                    spinner.ok("✔")

            except Exception:
                spinner.fail("✖")

        if format_type == "markdown":
            content_list = [
                f"URL: {url}\n\n{content}"
                for url, content in content_dict.items()
            ]
            return "\n\n---\n\n".join(content_list)

        return content_dict

    def extract(
        self,
        base_url: str,
        output_format,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        model: str = "gpt-4o-mini",
        max_depth: int = 0,
    ) -> BaseModel:
        """
        Extract information from a site by crawling it.

        Args:
            base_url: The starting URL for crawling.
            output_format: The format of the output.
            api_key: The OpenAI API key.
            temperature: The temperature for the model.
            model: The model to use.
            max_depth: The maximum depth of the crawl.
        """

        api_key = api_key or os.environ.get("OPENAI_API_KEY")

        client = OpenAI(api_key=api_key)
        content_markdown = self.crawl(
            base_url, max_depth, format_type="markdown"
        )
        if not isinstance(content_markdown, str):
            raise ValueError("Content markdown must be a string")
        if content_markdown.strip() == "":
            raise ValueError("Content markdown is empty")

        with yaspin(text=f"Extracting: {base_url}") as spinner:
            response = client.beta.chat.completions.parse(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract the content from the following markdown",
                    },
                    {
                        "role": "user",
                        "content": content_markdown,
                    },
                ],
                temperature=temperature,
                response_format=output_format,
            )
            spinner.ok("✔")

        return output_format(**json.loads(response.choices[0].message.content))
