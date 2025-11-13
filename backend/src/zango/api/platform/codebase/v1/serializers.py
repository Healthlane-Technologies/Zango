from rest_framework import serializers


class FieldSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField()
    attributes = serializers.JSONField(required=False)
    related_model = serializers.CharField(required=False)


class ModelSerializer(serializers.Serializer):
    name = serializers.CharField()
    fields = FieldSerializer(many=True)
    relationships = FieldSerializer(many=True)
    meta = serializers.JSONField(required=False)


class RouteSerializer(serializers.Serializer):
    pattern = serializers.CharField(required=False, allow_blank=True)
    view = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    type = serializers.CharField(required=False, allow_blank=True)
    includes = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    full_pattern = serializers.CharField(required=False, allow_blank=True)
    module = serializers.CharField(required=False, allow_blank=True)
    package = serializers.CharField(required=False, allow_blank=True)
    url_file = serializers.CharField(required=False, allow_blank=True)
    children = serializers.ListField(required=False)


class ModuleSerializer(serializers.Serializer):
    name = serializers.CharField()
    path = serializers.CharField()

    # Additional fields that will be populated from analyzing the module
    models_count = serializers.IntegerField(required=False)
    views_count = serializers.IntegerField(required=False)
    templates_count = serializers.IntegerField(required=False)
    has_urls = serializers.BooleanField(required=False)
    has_policies = serializers.BooleanField(required=False)
    models = ModelSerializer(many=True, required=False)
    routes = RouteSerializer(many=True, required=False)


class PackageRouteSerializer(serializers.Serializer):
    re_path = serializers.CharField()
    package = serializers.CharField()
    url = serializers.CharField()


class AppRouteSerializer(serializers.Serializer):
    module = serializers.CharField()
    re_path = serializers.CharField()
    url = serializers.CharField()


class AppCodebaseSerializer(serializers.Serializer):
    app_name = serializers.CharField()
    version = serializers.CharField()
    modules = ModuleSerializer(many=True)
    package_routes = PackageRouteSerializer(many=True)
    app_routes = AppRouteSerializer(many=True)
    route_tree = serializers.JSONField(required=False)
    dot_diagram = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    # Summary statistics
    total_modules = serializers.IntegerField()
    total_packages = serializers.IntegerField()
    total_routes = serializers.IntegerField()

    # Workspace info
    workspace_path = serializers.CharField()
    settings_file_exists = serializers.BooleanField()
    last_modified = serializers.DateTimeField(required=False)
