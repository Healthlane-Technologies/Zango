from locust import HttpUser, task, between


class Loadtest(HttpUser):
    wait_time = between(1, 3)

    @task
    def test_mod_0(self):
        self.client.get("mod0/view1")

    @task
    def test_mod_1(self):
        self.client.get("mod1/view1/")

    @task
    def test_mod_2(self):
        self.client.get("mod2/view1")

    @task
    def test_mod_3(self):
        self.client.get("mod3/view1/")

    @task
    def test_mod_4(self):
        self.client.get("mod4/view1")

    @task
    def test_mod_5(self):
        self.client.get("mod5/view1/")

    @task
    def test_mod_6(self):
        self.client.get("mod6/view1")

    @task
    def test_mod_7(self):
        self.client.get("mod7/view1/")

    @task
    def test_mod_8(self):
        self.client.get("mod8/view1")

    @task
    def test_mod_9(self):
        self.client.get("mod9/view1/")

    @task
    def test_update_release(self):
        self.client.get("mod0/update_release")
