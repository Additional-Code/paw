# Paw

A Python package for web scraping, crawling, and structured data extraction using AI.

## Features

- **Scrape**: Convert web pages to clean markdown format
- **Crawl**: Navigate through websites and extract content from multiple pages
- **Extract**: Parse web content into structured data using OpenAI models

## Installation

```bash
🚧 under construction 🚧
```

## Usage

### Basic Scraping

```python
from paw import Paw

# Initialize the scraper
paw = Paw()

# Scrape a single page
markdown_content = paw.scrape("https://example.com")
print(markdown_content)
```

### Web Crawling

```python
from paw import Paw

# Initialize with custom settings
paw = Paw(
    delay=0.5,  # Time between requests
    ignore_links=False,  # Keep links in markdown
    ignore_images=True,  # Remove images
)

# Crawl a website (up to 2 levels deep)
content = paw.crawl(
    "https://example.com",
    max_depth=2,
    format_type="markdown"  # or "json"
)

print(content)
```

### Structured Data Extraction

```python
from paw import Paw
from pydantic import BaseModel
from typing import List

# Define your data model
class Post(BaseModel):
    title: str
    summary: str

class Author(BaseModel):
    name: str
    posts: List[Post]

# Extract structured data
paw = Paw()
author_data = paw.extract(
    "https://blog.example.com",
    output_format=Author,
    max_depth=1,
    model="gpt-4o-mini"  # OpenAI model to use
)

print(author_data.model_dump_json(indent=4))
```

## Configuration Options

The `Paw` class accepts the following parameters:

- `headers`: Custom HTTP headers (default includes a standard User-Agent)
- `delay`: Time in seconds between requests (default: 0.5)
- `ignore_links`: Remove hyperlinks from markdown output (default: True)
- `ignore_images`: Remove images from markdown output (default: True)
- `ignore_emphasis`: Remove emphasis (bold, italic) from markdown output (default: True)
- `ignore_tables`: Remove tables from markdown output (default: True)
- `ignore_mailto_links`: Remove mailto links from markdown output (default: True)
- `verbose`: Enable verbose logging (default: False)

## Requirements

- Python 3.12+
- Dependencies: beautifulsoup4, html2text, openai, pydantic, requests, yaspin

## License

[MIT License](LICENSE)
