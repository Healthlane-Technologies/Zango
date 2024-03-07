from locust import HttpUser, task, between
class Loadtest(HttpUser):
    wait_time = between(1,3)


    @task
    def test_mod_0(self):
        self.client.get('mod1/view0')

    @task
    def test_mod_1(self):
        self.client.get('mod1/view1')

    @task
    def test_mod_2(self):
        self.client.get('mod1/view2')

    @task
    def test_mod_3(self):
        self.client.get('mod1/view3')

    @task
    def test_mod_4(self):
        self.client.get('mod1/view4')

    @task
    def test_mod_5(self):
        self.client.get('mod1/view5')

    @task
    def test_mod_6(self):
        self.client.get('mod1/view6')

    @task
    def test_mod_7(self):
        self.client.get('mod1/view7')

    @task
    def test_mod_8(self):
        self.client.get('mod1/view8')

    @task
    def test_mod_9(self):
        self.client.get('mod1/view9')