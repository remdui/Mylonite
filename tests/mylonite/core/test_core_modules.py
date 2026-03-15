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
            (root / "default" / "templates").mkdir(parents=True)
            (root / "default" / "static").mkdir(parents=True)
            (root / "ocean" / "templates").mkdir(parents=True)
            (root / "ocean" / "static").mkdir(parents=True)

            paths = ThemeResolver(root).resolve(ThemeSettings(name="ocean"))

        self.assertEqual(paths.template_dir.parent.name, "ocean")
        self.assertEqual(paths.static_dir.parent.name, "ocean")

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
