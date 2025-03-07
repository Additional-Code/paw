from typing import List, Literal

DEFAULT_USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
)

FORMAT_TYPE = Literal["markdown", "json"]

TAG_TO_REMOVE: List[str] = [
    "script",
    "style",
    "meta",
    "link",
    "noscript",
    "iframe",
    "svg",
]
