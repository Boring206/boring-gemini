import pytest

from boring.skills_catalog import is_trusted_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/torvalds/linux", True),
        ("https://gist.github.com/user/123", True),
        ("https://gitlab.com/gitlab-org/gitlab", True),
        ("https://gitlab.com/group/subgroup/project", True),
        ("https://gitee.com/oschina/git", True),
        ("https://www.gitee.com/user/repo", True),
        ("http://skillsmp.com/skill", True),
        ("git@github.com:user/repo.git", True),  # urlparse netloc behavior for ssh?
        # Actually urlparse("git@github.com:...") often parses differently.
        # "git@github.com" is scheme="git@github.com" or netloc="" depending on python version/lib
        # Let's check typical install_command URL usage which is HTTPS.
        ("https://evil.com/repo", False),
        ("https://github.com.evil.com/repo", False),  # Subdomain checking
        ("https://gitlab.evil.com/repo", False),
    ],
)
def test_is_trusted_url(url, expected):
    # Note: is_trusted_url logic: domain == d or domain.endswith(f".{d}")
    # urlparse("https://github.com.evil.com").netloc -> "github.com.evil.com"
    # "github.com.evil.com".endswith(".github.com") -> False.
    # "github.com.evil.com" == "github.com" -> False.
    # So it should be safe.
    assert is_trusted_url(url) == expected
