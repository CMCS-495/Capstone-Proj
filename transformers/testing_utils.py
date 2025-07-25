"""Simplified testing utilities used in the test suite."""

import doctest
from _pytest.doctest import DoctestModule


class HfDocTestParser(doctest.DocTestParser):
    """Placeholder parser with minimal functionality."""
    pass


class HfDoctestModule(DoctestModule):
    """Thin wrapper around DoctestModule."""

    def collect(self):
        return super().collect()


def pytest_addoption_shared(parser):  # pragma: no cover - no-op
    """Add custom pytest options (stub)."""
    pass


def pytest_terminal_summary_main(tr, id):  # pragma: no cover - no-op
    """Emit terminal summaries (stub)."""
    pass
