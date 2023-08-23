from locust import HttpUser, task, between

class Loadtest(HttpUser):
    wait_time = between(1,3)

    @task(weight=100)
    def test_tenant(self):
        # with open("count.txt", "a+") as d:
        #     d.write("1\n")
        self.client.get("mod1/view2")
    