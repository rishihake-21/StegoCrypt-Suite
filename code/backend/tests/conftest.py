import sys
from pathlib import Path


def pytest_sessionstart(session):
    # Ensure Backend package is importable in tests
    root = Path(__file__).parent.parent
    backend = root / "Backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))


