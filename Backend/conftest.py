import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Seed a strong JWT_SECRET before the app/config is imported, so tests don't
# depend on the local .env and satisfy the minimum-length validator.
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-prod-1234567890")
