import shutil

def delete_modules(num, tenant_name):
    for i in range(num):
        shutil.rmtree(f"workspaces/{tenant_name}/mod{i}")

if __name__ == "__main__":
    delete_modules(100, "loadtest_0")