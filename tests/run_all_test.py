import os, sys
# insert the project root (one level up) onto sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import sys

def main():
    """Run all project tests and exit with appropriate status code."""
    exit_code = pytest.main(['-q', 'tests'])
    sys.exit(exit_code)

if __name__ == '__main__':
    main()