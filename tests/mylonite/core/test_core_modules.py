from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from mylonite.core.artifact_services import ArtifactBuildRequest
from mylonite.core.build_workflow import BuildInput, build_cache_key
from mylonite.core.content_schema import (
    PERSON_PROFILE_SCHEMA,
    SITE_CONFIG_SCHEMA,
    parse_boolean,
    schema_defaults,
    validate_record,
)
from mylonite.core.content_types import (
    ArtifactVisibility,
    ThemeSettings,
    ValidationStatus,
)
from mylonite.core.theme_loader import ThemeResolver


class CoreModulesTests(TestCase):
    @staticmethod
    def _create_theme(root: Path, theme_id: str) -> None:
        theme_root = root / theme_id
        (theme_root / "static").mkdir(parents=True)
        (theme_root / "theme.toml").write_text(
            '\n'.join(
                [
                    f'name = "{theme_id.title()}"',
                    f'description = "{theme_id} theme"',
                    'version = "1.0.0"',
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    def test_validation_status_to_dict(self):
        status = ValidationStatus(has_errors=True, errors=["site: site_url: required"])

        self.assertEqual(
            status.to_dict(),
            {"has_errors": True, "errors": ["site: site_url: required"]},
        )

    def test_schema_defaults_exposes_site_defaults(self):
        defaults = schema_defaults(SITE_CONFIG_SCHEMA)

        self.assertEqual(defaults["owner_id"], "identity.person.owner")
        self.assertTrue(defaults["footer_show_generated_by"])

    def test_parse_boolean_accepts_string_values(self):
        self.assertTrue(parse_boolean("true"))
        self.assertFalse(parse_boolean("false"))

    def test_schema_defaults_returns_detached_nested_defaults(self):
        defaults_a = schema_defaults(SITE_CONFIG_SCHEMA)
        defaults_b = schema_defaults(SITE_CONFIG_SCHEMA)

        defaults_a["theme"]["name"] = "custom"

        self.assertEqual(defaults_b["theme"]["name"], "default")

    def test_validate_record_reports_missing_required_field(self):
        normalized, errors = validate_record(
            PERSON_PROFILE_SCHEMA,
            {"id": "identity.person.owner"},
        )

        self.assertEqual(normalized["id"], "identity.person.owner")
        self.assertIn("full_name: required", errors)

    def test_theme_resolver_prefers_existing_requested_theme(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._create_theme(root, "default")
            self._create_theme(root, "ocean")

            resolved = ThemeResolver(root).resolve(ThemeSettings(name="ocean"))

        self.assertEqual(resolved.active_theme.theme_id, "ocean")
        self.assertEqual(resolved.active_theme.static_dir.parent.name, "ocean")

    def test_theme_resolver_reports_missing_required_static_assets(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._create_theme(root, "default")
            self._create_theme(root, "minimal")

            (root / "default" / "static" / "css").mkdir(parents=True, exist_ok=True)
            (root / "default" / "static" / "css" / "site.css").write_text(
                "body { color: red; }\n",
                encoding="utf-8",
            )

            resolved = ThemeResolver(root).resolve(ThemeSettings(name="minimal"))

        self.assertEqual(
            resolved.missing_required_static_files,
            ("css/site.css",),
        )

    def test_theme_resolver_ignores_invalid_theme_folders(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._create_theme(root, "default")
            (root / "broken-theme" / "static").mkdir(parents=True, exist_ok=True)

            themes = ThemeResolver(root).discover_themes()

        self.assertEqual([theme.theme_id for theme in themes], ["default"])

    def test_build_cache_key_changes_for_variant(self):
        base = BuildInput(site_id="site", content_version="1", theme_name="default")
        tailored = BuildInput(
            site_id="site",
            content_version="1",
            theme_name="default",
            artifact_variant="research",
        )

        self.assertNotEqual(build_cache_key(base), build_cache_key(tailored))

    def test_artifact_build_request_supports_visibility(self):
        request = ArtifactBuildRequest(
            profile_id="identity.person.owner",
            variant="general",
            output_format="pdf",
            visibility=ArtifactVisibility.PRIVATE,
        )

        self.assertEqual(request.visibility, ArtifactVisibility.PRIVATE)
