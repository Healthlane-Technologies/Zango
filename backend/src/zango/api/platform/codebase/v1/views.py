import ast
import json
import os
import traceback
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.utils.decorators import method_decorator

from zango.apps.shared.tenancy.models import TenantModel
from zango.core.api import (
    TenantMixin,
    ZangoGenericPlatformAPIView,
    get_api_response,
)
from zango.core.permissions import IsPlatformUserAllowedApp
from zango.core.common_utils import set_app_schema_path

from .serializers import AppCodebaseSerializer


@method_decorator(set_app_schema_path, name="dispatch")
class AppCodebaseViewAPIV1(ZangoGenericPlatformAPIView, TenantMixin):
    permission_classes = (IsPlatformUserAllowedApp,)

    def analyze_module(self, module_path):
        """Analyze a module directory for additional details"""
        module_info = {
            'models_count': 0,
            'views_count': 0,
            'templates_count': 0,
            'has_urls': False,
            'has_policies': False,
            'models': [],
            'routes': []
        }
        
        try:
            # Check for models.py
            models_file = module_path / 'models.py'
            if models_file.exists():
                model_details = self.extract_model_details(models_file)
                module_info['models_count'] = len(model_details)
                module_info['models'] = model_details
            
            # Check for views.py or views directory
            views_file = module_path / 'views.py'
            views_dir = module_path / 'views'
            if views_file.exists():
                module_info['views_count'] = 1
            elif views_dir.exists() and views_dir.is_dir():
                module_info['views_count'] = len(list(views_dir.glob('*.py')))
            
            # Check for templates directory
            templates_dir = module_path / 'templates'
            if templates_dir.exists() and templates_dir.is_dir():
                module_info['templates_count'] = len(list(templates_dir.rglob('*.html')))
            
            # Check for urls.py and extract routes
            urls_file = module_path / 'urls.py'
            module_info['has_urls'] = urls_file.exists()
            if urls_file.exists():
                module_info['routes'] = self.extract_routes_from_urls(urls_file)
            
            # Check for policies.json
            policies_file = module_path / 'policies.json'
            module_info['has_policies'] = policies_file.exists()
            
        except Exception as e:
            print(f"Error analyzing module {module_path}: {str(e)}")
        
        return module_info

    def extract_model_details(self, models_file):
        """Extract model details from a models.py file"""
        models = []
        
        try:
            with open(models_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the Python file
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a Django model (inherits from models.Model or similar)
                    is_model = False
                    for base in node.bases:
                        base_name = ""
                        if isinstance(base, ast.Name):
                            base_name = base.id
                        elif isinstance(base, ast.Attribute):
                            base_name = base.attr
                        
                        if 'Model' in base_name or 'AbstractModel' in base_name or 'Mixin' in base_name:
                            is_model = True
                            break
                    
                    if is_model:
                        model_info = {
                            'name': node.name,
                            'fields': [],
                            'relationships': [],
                            'meta': {}
                        }
                        
                        # Extract fields and relationships
                        for item in node.body:
                            if isinstance(item, ast.Assign):
                                for target in item.targets:
                                    if isinstance(target, ast.Name):
                                        field_info = self.analyze_field(target.id, item.value)
                                        if field_info:
                                            if field_info['type'] in ['ForeignKey', 'OneToOneField', 'ManyToManyField', 'ZForeignKey', 'ZOneToOneField', 'ZManyToManyField']:
                                                model_info['relationships'].append(field_info)
                                            else:
                                                model_info['fields'].append(field_info)
                            
                            # Extract Meta class info
                            elif isinstance(item, ast.ClassDef) and item.name == 'Meta':
                                for meta_item in item.body:
                                    if isinstance(meta_item, ast.Assign):
                                        for target in meta_item.targets:
                                            if isinstance(target, ast.Name):
                                                if target.id == 'db_table':
                                                    if isinstance(meta_item.value, ast.Constant):
                                                        model_info['meta']['db_table'] = meta_item.value.value
                                                elif target.id == 'verbose_name':
                                                    if isinstance(meta_item.value, ast.Constant):
                                                        model_info['meta']['verbose_name'] = meta_item.value.value
                        
                        models.append(model_info)
        
        except Exception as e:
            print(f"Error parsing models file {models_file}: {str(e)}")
        
        return models

    def extract_routes_from_urls(self, urls_file):
        """Extract route patterns from a urls.py file"""
        routes = []
        
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the Python file
            tree = ast.parse(content)
            
            # Look for urlpatterns list
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == 'urlpatterns':
                            # Extract routes from urlpatterns
                            if isinstance(node.value, ast.List):
                                for route_item in node.value.elts:
                                    route_info = self.analyze_route_pattern(route_item)
                                    if route_info:
                                        routes.append(route_info)
                            break
        
        except Exception as e:
            print(f"Error parsing urls file {urls_file}: {str(e)}")
        
        return routes
    
    def analyze_route_pattern(self, route_node):
        """Analyze a route pattern node (path() or re_path() call)"""
        route_info = {
            'pattern': '',
            'view': None,
            'name': None,
            'includes': None,
            'type': 'path'  # 'path' or 're_path' or 'include'
        }
        
        if isinstance(route_node, ast.Call):
            # Get function name (path, re_path, include)
            if isinstance(route_node.func, ast.Name):
                route_info['type'] = route_node.func.id
            
            # Extract pattern (first argument)
            if route_node.args:
                if isinstance(route_node.args[0], ast.Constant):
                    route_info['pattern'] = route_node.args[0].value
                
                # Extract view or include (second argument)
                if len(route_node.args) > 1:
                    if isinstance(route_node.args[1], ast.Name):
                        route_info['view'] = route_node.args[1].id
                    elif isinstance(route_node.args[1], ast.Attribute):
                        # Handle views.function_name or ViewClass.as_view()
                        if hasattr(route_node.args[1].value, 'id'):
                            route_info['view'] = f"{route_node.args[1].value.id}.{route_node.args[1].attr}"
                        else:
                            route_info['view'] = route_node.args[1].attr
                    elif isinstance(route_node.args[1], ast.Call):
                        # Handle ViewClass.as_view() or include() calls
                        if isinstance(route_node.args[1].func, ast.Attribute):
                            if route_node.args[1].func.attr == 'as_view':
                                # This is a class-based view
                                if isinstance(route_node.args[1].func.value, ast.Name):
                                    route_info['view'] = f"{route_node.args[1].func.value.id}.as_view()"
                            else:
                                route_info['view'] = f"{route_node.args[1].func.value.id}.{route_node.args[1].func.attr}"
                        elif isinstance(route_node.args[1].func, ast.Name) and route_node.args[1].func.id == 'include':
                            if route_node.args[1].args:
                                if isinstance(route_node.args[1].args[0], ast.Constant):
                                    route_info['includes'] = route_node.args[1].args[0].value
                                elif isinstance(route_node.args[1].args[0], ast.Attribute):
                                    route_info['includes'] = f"{route_node.args[1].args[0].value.id}.{route_node.args[1].args[0].attr}"
            
            # Extract name from keyword arguments
            for keyword in route_node.keywords:
                if keyword.arg == 'name' and isinstance(keyword.value, ast.Constant):
                    route_info['name'] = keyword.value.value
            
            return route_info
        
        return None

    def analyze_field(self, field_name, field_node):
        """Analyze a field node to extract field information"""
        field_info = {'name': field_name, 'type': 'Unknown', 'attributes': {}}
        
        if isinstance(field_node, ast.Call):
            # Get field type
            if isinstance(field_node.func, ast.Attribute):
                field_info['type'] = field_node.func.attr
            elif isinstance(field_node.func, ast.Name):
                field_info['type'] = field_node.func.id
            
            # Extract field attributes
            for keyword in field_node.keywords:
                if keyword.arg == 'max_length' and isinstance(keyword.value, ast.Constant):
                    field_info['attributes']['max_length'] = keyword.value.value
                elif keyword.arg == 'null' and isinstance(keyword.value, ast.Constant):
                    field_info['attributes']['null'] = keyword.value.value
                elif keyword.arg == 'blank' and isinstance(keyword.value, ast.Constant):
                    field_info['attributes']['blank'] = keyword.value.value
                elif keyword.arg == 'default':
                    if isinstance(keyword.value, ast.Constant):
                        field_info['attributes']['default'] = keyword.value.value
                elif keyword.arg == 'related_name' and isinstance(keyword.value, ast.Constant):
                    field_info['attributes']['related_name'] = keyword.value.value
                elif keyword.arg == 'on_delete':
                    if isinstance(keyword.value, ast.Attribute):
                        field_info['attributes']['on_delete'] = keyword.value.attr
            
            # For relationship fields, try to get the related model
            if field_info['type'] in ['ForeignKey', 'OneToOneField', 'ManyToManyField', 'ZForeignKey', 'ZOneToOneField', 'ZManyToManyField']:
                if field_node.args:
                    if isinstance(field_node.args[0], ast.Name):
                        field_info['related_model'] = field_node.args[0].id
                    elif isinstance(field_node.args[0], ast.Constant):
                        field_info['related_model'] = field_node.args[0].value
                    elif isinstance(field_node.args[0], ast.Attribute):
                        field_info['related_model'] = f"{field_node.args[0].value.id}.{field_node.args[0].attr}"
                    elif isinstance(field_node.args[0], ast.Call):
                        # Handle cases like ForeignKey(to='ModelName') or model references
                        for keyword in field_node.args[0].keywords:
                            if keyword.arg == 'to' and isinstance(keyword.value, ast.Constant):
                                field_info['related_model'] = keyword.value.value
                                break
                
                # If still no related model found, check 'to' keyword argument
                if 'related_model' not in field_info:
                    for keyword in field_node.keywords:
                        if keyword.arg == 'to' and isinstance(keyword.value, ast.Constant):
                            field_info['related_model'] = keyword.value.value
                            break
            
            return field_info
        
        return None

    def build_route_tree(self, workspace_path, app_routes, package_routes, modules):
        """Build a hierarchical route tree from all available route information"""
        route_tree = {
            'root': '/',
            'children': []
        }
        
        # Process app routes
        for route in app_routes:
            route_node = {
                'pattern': route['re_path'],
                'module': route['module'],
                'type': 'app_route',
                'url_file': route['url'],
                'children': []
            }
            
            # Find and process nested routes from the module
            for module in modules:
                if module['name'] == route['module'] and module.get('routes'):
                    for module_route in module['routes']:
                        # Combine parent and child patterns
                        full_pattern = route['re_path'].rstrip('/') + '/' + module_route['pattern'].lstrip('/')
                        child_node = {
                            'pattern': module_route['pattern'],
                            'full_pattern': full_pattern,
                            'view': module_route.get('view'),
                            'name': module_route.get('name'),
                            'type': module_route.get('type', 'path'),
                            'includes': module_route.get('includes'),
                            'children': []
                        }
                        
                        # If this route includes another URL file, try to process it
                        if module_route.get('includes'):
                            child_node['children'] = self.process_included_urls(
                                workspace_path, route['module'], module_route['includes']
                            )
                        
                        route_node['children'].append(child_node)
            
            route_tree['children'].append(route_node)
        
        # Process package routes
        for route in package_routes:
            route_node = {
                'pattern': route['re_path'],
                'package': route['package'],
                'type': 'package_route',
                'url_file': route['url'],
                'children': []
            }
            route_tree['children'].append(route_node)
        
        return route_tree
    
    def process_included_urls(self, workspace_path, module_name, includes):
        """Process included URL patterns from an include() statement"""
        children = []
        
        try:
            # Try to resolve the include path
            if '.' in includes:
                # It's a module path like 'myapp.views.api_urls'
                parts = includes.split('.')
                include_path = workspace_path / module_name / '/'.join(parts[1:]) + '.py'
            else:
                # It's a simple filename
                include_path = workspace_path / module_name / includes
                if not include_path.suffix:
                    include_path = include_path.with_suffix('.py')
            
            if include_path.exists():
                nested_routes = self.extract_routes_from_urls(include_path)
                for route in nested_routes:
                    child_node = {
                        'pattern': route['pattern'],
                        'view': route.get('view'),
                        'name': route.get('name'),
                        'type': route.get('type', 'path'),
                        'includes': route.get('includes'),
                        'children': []
                    }
                    
                    # Recursively process includes
                    if route.get('includes'):
                        child_node['children'] = self.process_included_urls(
                            workspace_path, module_name, route['includes']
                        )
                    
                    children.append(child_node)
        
        except Exception as e:
            print(f"Error processing included URLs {includes}: {str(e)}")
        
        return children

    def get(self, request, *args, **kwargs):
        try:
            # Get the app tenant
            tenant = self.get_tenant(**kwargs)
            app_name = tenant.schema_name
            
            # Construct workspace path
            workspace_path = Path(settings.BASE_DIR) / 'workspaces' / app_name
            settings_file_path = workspace_path / 'settings.json'
            
            if not workspace_path.exists():
                return get_api_response(
                    False,
                    {"message": f"Workspace directory not found for app: {app_name}"},
                    404
                )
            
            response_data = {
                'app_name': app_name,
                'workspace_path': str(workspace_path),
                'settings_file_exists': settings_file_path.exists(),
            }
            
            if settings_file_path.exists():
                # Read and parse settings.json
                with open(settings_file_path, 'r') as f:
                    settings_data = json.load(f)
                
                # Get file modification time
                stat = os.stat(settings_file_path)
                response_data['last_modified'] = datetime.fromtimestamp(stat.st_mtime)
                
                # Process settings data
                response_data['version'] = settings_data.get('version', 'unknown')
                
                # Process modules with additional analysis
                modules = settings_data.get('modules', [])
                for module in modules:
                    module_path = workspace_path / module['path']
                    if module_path.exists():
                        module_analysis = self.analyze_module(module_path)
                        module.update(module_analysis)
                
                response_data['modules'] = modules
                response_data['package_routes'] = settings_data.get('package_routes', [])
                response_data['app_routes'] = settings_data.get('app_routes', [])
                
                # Build route tree
                response_data['route_tree'] = self.build_route_tree(
                    workspace_path,
                    settings_data.get('app_routes', []),
                    settings_data.get('package_routes', []),
                    modules
                )
                
                # Calculate statistics
                response_data['total_modules'] = len(modules)
                response_data['total_packages'] = len(set(
                    route['package'] for route in settings_data.get('package_routes', [])
                ))
                response_data['total_routes'] = (
                    len(settings_data.get('package_routes', [])) + 
                    len(settings_data.get('app_routes', []))
                )
            else:
                # If settings.json doesn't exist, try to scan the workspace
                response_data['version'] = 'unknown'
                response_data['modules'] = []
                response_data['package_routes'] = []
                response_data['app_routes'] = []
                response_data['total_modules'] = 0
                response_data['total_packages'] = 0
                response_data['total_routes'] = 0
            
            # Serialize the response
            serializer = AppCodebaseSerializer(data=response_data)
            if serializer.is_valid():
                return get_api_response(
                    True,
                    {
                        "app_codebase": serializer.data,
                        "message": "App codebase details fetched successfully"
                    },
                    200
                )
            else:
                return get_api_response(
                    False,
                    {"message": "Error serializing data", "errors": serializer.errors},
                    400
                )
                
        except Exception as e:
            traceback.print_exc()
            return get_api_response(
                False,
                {"message": str(e)},
                500
            )