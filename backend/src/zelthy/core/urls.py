

def z_include(module):
    from django.db import connection
    from django.urls import include
    result = include(f'workspaces.{connection.tenant.name}.{module}')
    return result