import os

import pytest

# Tests always run offline with the deterministic mock provider.
os.environ["LLM_PROVIDER"] = "mock"
os.environ["IAM_SOURCE"] = "snapshot"

from clouddesk import db  # noqa: E402


@pytest.fixture
def conn():
    c = db.connect(":memory:")
    yield c
    c.close()
