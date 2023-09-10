from locust import HttpUser, task, between
class Loadtest(HttpUser):
    wait_time = between(1,3)


    @task
    def test_mod_0(self):
        # self.client.get('admin/')
        self.client.get('mod1/view2/1/')