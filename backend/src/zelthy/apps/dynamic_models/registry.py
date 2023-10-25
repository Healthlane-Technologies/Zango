import threading

class TenantAppsRegistry:

    """
        Registry of all tenant Apps. Maintains the Configs of all TenantApps
        Updates TenantAppConfigs when tenantApp is changed via signal
        Singleton Object
    
    """
    tenant_apps = []
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        







