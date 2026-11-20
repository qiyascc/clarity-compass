import pytest

from clarity_persistence.secrets import SecretBox, SiteLogin


def test_box_roundtrip_and_wrong_key() -> None:
    sealed = SecretBox("key").seal(b"hunter2")
    assert b"hunter2" not in sealed
    assert SecretBox("key").open(sealed) == b"hunter2"
    with pytest.raises(ValueError, match="decrypt"):
        SecretBox("other").open(sealed)


def test_site_login_roundtrip_hides_the_password() -> None:
    box = SecretBox("key")
    login = SiteLogin("https://shop.test/login", "me@shop.test", "hunter2", submit_selector="#go")
    restored = SiteLogin.open(box, login.seal(box))
    assert restored == login
    assert "hunter2" not in repr(restored)


def test_extra_fields_are_ignored() -> None:
    box = SecretBox("key")
    sealed = box.seal(b'{"login_url": "u", "username": "n", "password": "p", "note": "x"}')
    assert SiteLogin.open(box, sealed).username == "n"
