import os, sys
import pytest

# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TablePlugin:
    def __init__(self):
        self.results = []

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            nodeid = report.nodeid
            location = report.location[0]
            outcome = report.outcome
            self.results.append((nodeid, location, outcome))

    def pytest_sessionfinish(self, session, exitstatus):
        if not self.results:
            return
        # compute column widths
        max_test = max(len(r[0]) for r in self.results + [("Test", "", "")])
        
        # header
        print()
        print(f"{'Test'.ljust(max_test)} Result")
        print(f"{'-'*max_test} {'-'*6}")
        # rows
        for test, inp, result in self.results:
            print(f"{test.ljust(max_test)}  {result}")


def main():
    """Run all project tests and print summary table."""
    tests_dir = os.path.join(os.path.dirname(__file__))
    plugin = TablePlugin()
    exit_code = pytest.main([
        '-q',
        '-p', 'no:pytest-ansible',
        tests_dir
    ], plugins=[plugin])
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
