from django.urls import reverse
from shared.torngit import Github
from codecov_auth.helpers import decode_token_from_cookie
from codecov_auth.models import Session
from django.conf import settings
from django.http.cookie import SimpleCookie


def test_get_github_redirect(client):
    url = reverse("github-login")
    res = client.get(url)
    assert res.status_code == 302
    assert (
        res.url
        == "https://github.com/login/oauth/authorize?response_type=code&scope=user%3Aemail%2Cread%3Aorg%2Crepo%3Astatus%2Cwrite%3Arepo_hook&client_id=3d44be0e772666136a13"
    )


def test_get_github_redirect_with_ghpr_cookie(client):
    client.cookies = SimpleCookie({"ghpr": "true"})
    url = reverse("github-login")
    res = client.get(url)
    assert res.status_code == 302
    assert (
        res.url
        == "https://github.com/login/oauth/authorize?response_type=code&scope=user%3Aemail%2Cread%3Aorg%2Crepo%3Astatus%2Cwrite%3Arepo_hook%2Crepo&client_id=3d44be0e772666136a13"
    )
    assert "ghpr" in res.cookies
    ghpr_cooke = res.cookies["ghpr"]
    assert ghpr_cooke.value == "true"
    assert ghpr_cooke.get("domain") == "codecov.io"


def test_get_github_already_with_code(client, mocker, db):
    async def helper_func(*args, **kwargs):
        return {
            "login": "ThiagoCodecov",
            "id": 44376991,
            "access_token": "testh04ph89fx0nkd3diauxcw75fyiuo3b86fw4j",
        }

    mocker.patch.object(Github, "get_authenticated_user", side_effect=helper_func)
    url = reverse("github-login")
    res = client.get(url, {"code": "aaaaaaa"})
    assert res.status_code == 302
    assert "github-token" in res.cookies
    assert "github-username" in res.cookies
    token_cookie = res.cookies["github-token"]
    username_cookie = res.cookies["github-username"]
    cookie_token = decode_token_from_cookie(settings.COOKIE_SECRET, token_cookie.value)
    assert username_cookie.value == "ThiagoCodecov"
    assert username_cookie.get("domain") == "codecov.io"
    assert token_cookie.get("domain") == "codecov.io"
    session = Session.objects.get(token=cookie_token)
    owner = session.owner
    assert owner.username == "ThiagoCodecov"
    assert owner.service_id == "44376991"
    assert res.url == "/redirect_app"
