import time
from django.test.runner import DiscoverRunner

class TimingDiscoverRunner(DiscoverRunner):
    def get_resultclass(self):
        return TimingTextTestResult

class TimingTextTestResult(DiscoverRunner.test_runner().resultclass):
    def startTest(self, test):
        self._started_at = time.time()
        super().startTest(test)

    def addSuccess(self, test):
        elapsed = time.time() - self._started_at
        name = self.getDescription(test)
        self.stream.writeln(f"\n{name} ... ok ({elapsed:.3f}s)")
        super().addSuccess(test)