"""Entity body-source strategies.

This module defines how an entity's large body text is represented:
- no separate body file (`NoBodySourceSpec`), or
- a body file mapped to a schema field (`FieldBodySourceSpec`).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


class BodySourceSpec(ABC):
    """Contract for mapping body text between storage and schema payloads."""

    @property
    @abstractmethod
    def text_filename(self) -> str | None:
        """Return body filename (without path) or ``None`` for no body file."""

    @abstractmethod
    def merge_payload(self, entry: dict, body: str) -> dict:
        """Merge entry data and body text into one payload for validation/mapping."""

    @abstractmethod
    def split_scaffold(self, entry_defaults: dict) -> tuple[dict, str | None]:
        """Split defaults into entry fields and optional text body scaffold content."""


@dataclass(frozen=True)
class NoBodySourceSpec(BodySourceSpec):
    """Body strategy for entities that only use ``entry.toml`` fields."""

    @property
    def text_filename(self) -> str | None:
        return None

    def merge_payload(self, entry: dict, body: str) -> dict:
        return dict(entry)

    def split_scaffold(self, entry_defaults: dict) -> tuple[dict, str | None]:
        return dict(entry_defaults), None


@dataclass(frozen=True)
class FieldBodySourceSpec(BodySourceSpec):
    """Body strategy for entities that store markdown in ``text/<filename>``."""

    field_name: str
    filename: str

    @property
    def text_filename(self) -> str | None:
        return self.filename

    def merge_payload(self, entry: dict, body: str) -> dict:
        payload = dict(entry)
        payload[self.field_name] = body
        return payload

    def split_scaffold(self, entry_defaults: dict) -> tuple[dict, str | None]:
        entry = dict(entry_defaults)
        body = str(entry.pop(self.field_name, ""))
        return entry, body
