"""Public (any platform user) read APIs over the published template catalogue."""

from __future__ import annotations

import logging

from zango.core.api import ZangoGenericPlatformAPIView, get_api_response

from .serializers import apps_using_counts, template_detail, template_summary


log = logging.getLogger("zango.app_templates")


def _published():
    from zango.apps.shared.app_templates.models import (
        AppTemplate,
        TemplateStatus,
        VersionStatus,
    )

    return (
        AppTemplate.objects.select_related("current_version")
        .filter(
            status=TemplateStatus.PUBLISHED,
            current_version__isnull=False,
            current_version__status=VersionStatus.PUBLISHED,
        )
        .order_by("sort_order", "name")
    )


class TemplateListView(ZangoGenericPlatformAPIView):
    """GET /api/v1/platform/app-templates/templates/?category=&q="""

    def get(self, request, *args, **kwargs):
        try:
            qs = _published()
            category = (request.GET.get("category") or "").strip()
            if category:
                qs = qs.filter(category__iexact=category)
            q = (request.GET.get("q") or "").strip().lower()
            counts = apps_using_counts()
            templates = []
            for template in qs:
                summary = template_summary(
                    template, template.current_version, counts.get(template.pk, 0)
                )
                if (
                    q
                    and q
                    not in " ".join(
                        [
                            summary["name"],
                            summary["one_liner"],
                            summary["category"],
                            summary["catalogue"]["description"],
                        ]
                    ).lower()
                ):
                    continue
                templates.append(summary)
            return get_api_response(True, {"templates": templates}, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("app_templates: list failed")
            return get_api_response(False, {"message": str(exc)}, 500)


class TemplateDetailView(ZangoGenericPlatformAPIView):
    """GET /api/v1/platform/app-templates/templates/<slug>/"""

    def get(self, request, slug, *args, **kwargs):
        try:
            template = _published().filter(slug=slug).first()
            if template is None:
                return get_api_response(False, {"message": "No such template."}, 404)
            counts = apps_using_counts()
            data = template_detail(
                template, template.current_version, counts.get(template.pk, 0)
            )
            return get_api_response(True, {"template": data}, 200)
        except Exception as exc:  # noqa: BLE001
            log.exception("app_templates: detail failed")
            return get_api_response(False, {"message": str(exc)}, 500)


class TemplateBuilderView(ZangoGenericPlatformAPIView):
    """GET templates/<slug>/versions/<version_uuid>/builder/

    What the console's builder panel renders a spec with. Published versions
    never change, so clients may cache the response for good. Deprecated
    versions still resolve: apps built on them are pinned to them.
    """

    def get(self, request, slug, version_uuid, *args, **kwargs):
        from zango.apps.shared.app_templates.models import (
            AppTemplateVersion,
            VersionStatus,
        )

        try:
            version = (
                AppTemplateVersion.objects.select_related("template")
                .filter(template__slug=slug, object_uuid=version_uuid)
                .exclude(status=VersionStatus.DRAFT)
                .first()
            )
            if version is None:
                return get_api_response(
                    False, {"message": "No such template version."}, 404
                )
            return get_api_response(
                True,
                {
                    "slug": version.template.slug,
                    "version": version.version,
                    "version_uuid": str(version.object_uuid),
                    "json_schema": version.json_schema,
                    "ui_schema": version.ui_schema,
                    "rules": version.rules,
                    "spec_root": version.spec_root,
                    "spec_format": version.spec_format,
                    "starter_yaml": version.starter_yaml,
                    "example_yaml": version.example_yaml,
                    "builder_url": (
                        f"/api/v1/platform/app-templates/templates/{version.template.slug}"
                        f"/versions/{version.object_uuid}/builder.html"
                        if version.has_builder
                        else None
                    ),
                },
                200,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("app_templates: builder failed")
            return get_api_response(False, {"message": str(exc)}, 500)


class TemplateBuilderPageView(ZangoGenericPlatformAPIView):
    """GET templates/<slug>/versions/<version_uuid>/builder.html

    The template's own builder page with the platform adapter injected. The
    console fetches it and renders it in a sandboxed iframe (scripts only, no
    same-origin access). Immutable per version.
    """

    def get(self, request, slug, version_uuid, *args, **kwargs):
        from django.http import HttpResponse

        from zango.apps.shared.app_templates.models import (
            AppTemplateVersion,
            VersionStatus,
        )
        from zango.apps.shared.app_templates.services.builder import compose

        version = (
            AppTemplateVersion.objects.select_related("template")
            .filter(template__slug=slug, object_uuid=version_uuid)
            .exclude(status=VersionStatus.DRAFT)
            .first()
        )
        if version is None or not version.has_builder:
            return get_api_response(
                False, {"message": "No builder for this template version."}, 404
            )
        response = HttpResponse(
            compose(version), content_type="text/html; charset=utf-8"
        )
        response["Cache-Control"] = "private, max-age=31536000, immutable"
        response["X-Content-Type-Options"] = "nosniff"
        # Opened directly (not via the console's sandboxed iframe) it must still
        # get an opaque origin: superadmin-authored script, never the console's.
        response["Content-Security-Policy"] = (
            "sandbox allow-scripts allow-downloads allow-popups allow-modals"
        )
        return response
