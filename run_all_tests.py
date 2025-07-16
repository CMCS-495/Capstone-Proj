import pytest
import sys


def main():
    """Run all project tests and exit with appropriate status code."""
    exit_code = pytest.main(['-q', 'tests'])
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
