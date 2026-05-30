import os
import sys


os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

BACK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACK_DIR not in sys.path:
    sys.path.insert(0, BACK_DIR)