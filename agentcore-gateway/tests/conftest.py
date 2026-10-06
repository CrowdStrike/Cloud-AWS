import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class FakeContext:
    """Minimal Lambda context mock."""
    aws_request_id = "test-request-id"
    client_context = None
