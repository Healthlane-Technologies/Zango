import shutil

def delete_modules(tenants):
        for tenant in tenants:
            shutil.rmtree(tenant)

if __name__ == "__main__":
    tenant_num = 2
    tenants = [f"loadtest_{i}" for i in range(tenant_num)]
    delete_modules(tenants)