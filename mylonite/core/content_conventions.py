"""Shared naming conventions and canonical identifiers for content entities."""

DEFAULT_OWNER_ID = "identity.person.owner"
DEFAULT_HOMEPAGE_MAIN_ID = "content.homepage.main"

ENTITY_TYPE_PERSON = "person"
ENTITY_TYPE_HOMEPAGE_MAIN = "homepage_main"

HOMEPAGE_MAIN_TEXT_FILENAME = "main.md"


def is_valid_entity_id(object_id: str) -> bool:
    """Allow dotted IDs only; block path traversal or empty segments."""
    if not object_id:
        return False
    if "/" in object_id or "\\" in object_id:
        return False
    parts = object_id.split(".")
    return all(part.strip() for part in parts)
