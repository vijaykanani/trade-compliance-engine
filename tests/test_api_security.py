import pytest

from app.security import valid_demo_api_secret


@pytest.mark.parametrize(
    ("expected", "supplied", "valid"),
    [
        ("shared-secret", "shared-secret", True),
        ("shared-secret", "wrong-secret", False),
        ("shared-secret", "", False),
        ("", "shared-secret", False),
    ],
)
def test_demo_api_secret_validation(expected, supplied, valid):
    assert valid_demo_api_secret(expected, supplied) is valid