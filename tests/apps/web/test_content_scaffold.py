from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from apps.web.content_entities import FieldBodySourceSpec, NoBodySourceSpec
from apps.web.content_registry import ContentEntityRegistry, EntityDefinition
from apps.web.content_scaffold import sync_content_examples
from mylonite.core.content_schema import FieldRule, SchemaDefinition
from mylonite.core.toml_utils import render_toml


class ContentScaffoldTests(TestCase):
    def test_render_toml_supports_nested_tables(self):
        rendered = render_toml(
            {
                "site_title": "Example",
                "theme": {
                    "name": "default",
                    "options": {
                        "contrast": "high",
                    },
                },
            }
        )

        self.assertIn('site_title = "Example"', rendered)
        self.assertIn("[theme]", rendered)
        self.assertIn('name = "default"', rendered)
        self.assertIn("[theme.options]", rendered)
        self.assertIn('contrast = "high"', rendered)

    def test_sync_prunes_stale_text_example_when_body_removed(self):
        schema_with_markdown = SchemaDefinition(
            schema_name="with_body",
            fields=(
                FieldRule("id", default="content.example.page"),
                FieldRule("title", default="Title"),
                FieldRule("markdown", default="Body"),
            ),
        )
        schema_without_markdown = SchemaDefinition(
            schema_name="without_body",
            fields=(
                FieldRule("id", default="content.example.page"),
                FieldRule("title", default="Title"),
            ),
        )

        with TemporaryDirectory() as tmp:
            root = Path(tmp)

            registry_with_body = ContentEntityRegistry(
                definitions={
                    "example": EntityDefinition(
                        entity_type="example",
                        mapper=lambda object_id, entry, body: entry,
                        body_source=FieldBodySourceSpec(
                            field_name="markdown",
                            filename="main.md",
                        ),
                        schema=schema_with_markdown,
                        example_object_ids=("content.example.page",),
                    )
                }
            )
            sync_content_examples(root, registry_with_body)

            generated_text = (
                root / "entities" / "content.example.page" / "text" / "main.md.example"
            )
            self.assertTrue(generated_text.exists())

            registry_without_body = ContentEntityRegistry(
                definitions={
                    "example": EntityDefinition(
                        entity_type="example",
                        mapper=lambda object_id, entry, body: entry,
                        body_source=NoBodySourceSpec(),
                        schema=schema_without_markdown,
                        example_object_ids=("content.example.page",),
                    )
                }
            )
            sync_content_examples(root, registry_without_body)

            self.assertFalse(generated_text.exists())

    def test_sync_rejects_invalid_object_id(self):
        invalid_schema = SchemaDefinition(
            schema_name="invalid",
            fields=(FieldRule("id", default="bad/id"),),
        )

        registry = ContentEntityRegistry(
            definitions={
                "bad": EntityDefinition(
                    entity_type="bad",
                    mapper=lambda object_id, entry, body: entry,
                    body_source=NoBodySourceSpec(),
                    schema=invalid_schema,
                    example_object_ids=("bad/id",),
                )
            }
        )

        with TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                sync_content_examples(Path(tmp), registry)
