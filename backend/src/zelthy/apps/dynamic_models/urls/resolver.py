class URLResolver:
    def __init__(self, tenant, path):
        self.tenant = tenant
        self.path = path

    def get_subapp(self, path):
        pass
