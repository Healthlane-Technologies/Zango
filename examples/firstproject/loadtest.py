from locust import HttpUser, task, between

class Loadtest(HttpUser):
    wait_time = between(1, 5)

    @task
    def test_tenant(self):
        self.client.get("mod1/view1/2/")
    