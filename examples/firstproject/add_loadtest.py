def add_loadtest(num):

    for i in range(2, num+2):
        with open("loadtest.py", "a") as f:
            f.write("\n\n")
            f.write("    @task\n")
            f.write(f"    def test_mod_{i}(self):\n")
            f.write(f"        self.client.get('mod{i}/view1')")

if __name__ == "__main__":
    add_loadtest(100)