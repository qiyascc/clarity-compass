import pytest

from clarity_core.net.urls import InvalidUrlError, normalize_url, same_site


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("theqiyas.cc", "https://theqiyas.cc/"),
        ("  HTTPS://TheQiyas.CC/About#team ", "https://theqiyas.cc/About"),
        ("http://theqiyas.cc:80/a?b=1", "http://theqiyas.cc/a?b=1"),
        ("https://theqiyas.cc:443", "https://theqiyas.cc/"),
        ("https://theqiyas.cc:8443/x", "https://theqiyas.cc:8443/x"),
        ("https://bücher.de/", "https://xn--bcher-kva.de/"),
        ("http://[2606:4700::1]:8080/", "http://[2606:4700::1]:8080/"),
    ],
)
def test_normalize_url(raw: str, expected: str) -> None:
    assert normalize_url(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "ftp://theqiyas.cc/",
        "javascript:alert(1)",
        "file:///etc/passwd",
        "https://user:pass@theqiyas.cc/",
        "https:///nohost",
        "https://theqiyas.cc:99999/",
    ],
)
def test_normalize_url_rejects(raw: str) -> None:
    with pytest.raises(InvalidUrlError):
        normalize_url(raw)


def test_same_site_ignores_www_and_scheme() -> None:
    assert same_site("https://www.theqiyas.cc/a", "http://theqiyas.cc/b")
    assert not same_site("https://theqiyas.cc/", "https://theqiyas.cc.evil.com/")
