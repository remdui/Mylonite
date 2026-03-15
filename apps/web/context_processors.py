from django.urls import reverse


def theme_assets(_request):
    return {
        "theme_css_url": reverse(
            "theme_static",
            kwargs={"asset_path": "css/site.css"},
        )
    }
