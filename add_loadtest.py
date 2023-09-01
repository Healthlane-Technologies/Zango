import sys


def add_loadtest_django(num):
    with open("loadtest.py", "w") as f:
        f.write("from locust import HttpUser, task, between\n")
        f.write("class Loadtest(HttpUser):\n")
        f.write("    wait_time = between(1,3)\n")
        for i in range(num):
            f.write("\n\n")
            f.write("    @task\n")
            f.write(f"    def test_mod_{i}(self):\n")
            f.write(f"        self.client.get('mod1/view{i}')")

def add_loadtest_zelthy(num):
    with open("loadtest.py", "w") as f:
        f.write("from locust import HttpUser, task, between\n")
        f.write("class Loadtest(HttpUser):\n")
        f.write("    wait_time = between(1,3)\n")
        for i in range(num):
            f.write("\n\n")
            f.write("    @task\n")
            f.write(f"    def test_mod_{i}(self):\n")
            f.write(f"        self.client.get('mod{i}/view1')")

if __name__ == "__main__":
    platform = sys.argv[1]
    tests = int(sys.argv[2])
    if platform == "django":
        add_loadtest_django(tests)
    if platform == "zelthy":
        add_loadtest_zelthy(tests)