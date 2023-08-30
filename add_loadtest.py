def add_loadtest(num):
    with open("loadtest.py", "w") as f:
        f.write("from locust import HttpUser, task, between\n")
        f.write("class Loadtest(HttpUser):\n")
        f.write("    wait_time = between(1,3)\n")
        for i in range(2, num+2):
            f.write("\n\n")
            f.write("    @task\n")
            f.write(f"    def test_mod_{i}(self):\n")
            f.write(f"        self.client.get('mod{i}/view1')")

if __name__ == "__main__":
    add_loadtest(100)