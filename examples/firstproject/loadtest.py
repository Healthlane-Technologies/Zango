from locust import HttpUser, task

class Loadtest(HttpUser):

    @task
    def test_tenant(self):
        self.client.get("mod1/view1/2/")
    