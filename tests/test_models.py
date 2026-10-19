"""Unit tests for the User model's password handling.

The spec requires passwords to be hashed, never stored in clear. These tests
pin that intent at the model level: a password can be set and verified, but
never read back.
"""

import pytest

from app.models import User


def _user():
    return User(email="a@example.com", name="Alice Martin")


def test_setting_password_stores_a_hash_not_the_plaintext():
    # Setting the password must transform it: the raw value must not survive.
    user = _user()
    user.password = "StrongPass123"

    assert user._password_hash  # something was stored
    assert user._password_hash != "StrongPass123"  # and it is not the plaintext


def test_password_cannot_be_read_back():
    # Write-only by design: once set, the password cannot be read out again.
    user = _user()
    user.password = "StrongPass123"

    with pytest.raises(AttributeError):
        _ = user.password


def test_check_password_accepts_the_right_one_and_rejects_others():
    # The hash is only useful if it can later confirm the correct password
    # and reject anything else.
    user = _user()
    user.password = "StrongPass123"

    assert user.check_password("StrongPass123") is True
    assert user.check_password("WrongPass999") is False
