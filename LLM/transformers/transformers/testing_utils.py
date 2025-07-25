"""Simplified testing utilities for the transformer tests."""

import doctest
from _pytest.doctest import DoctestModule


class HfDocTestParser(doctest.DocTestParser):
    pass


class HfDoctestModule(DoctestModule):
    def collect(self):
        return super().collect()


def pytest_addoption_shared(parser):
    pass


def pytest_terminal_summary_main(tr, id):
    pass
