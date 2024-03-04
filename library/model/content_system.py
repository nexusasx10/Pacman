from typing import Any


class ContentAttribute:
    id: str
    value: Any


class ContentEntry:
    id: str
    attributes: list[ContentAttribute]


class ContentLibrary:
    content_entries: ContentEntry
