import pytest

from clouddesk.kb import default_kb, tokenize


def test_tokenize_drops_stopwords_and_plurals():
    assert tokenize("The VPN disconnects for users") == ["vpn", "disconnect", "user"]


@pytest.mark.parametrize("query, expected", [
    ("I am locked out of my account after changing my password", "account-lockout"),
    ("AccessDenied: not authorized to perform lambda:UpdateFunctionCode", "aws-accessdenied"),
    ("VPN keeps disconnecting when working from home", "vpn"),
    ("shared mailbox does not show up in Outlook", "shared-mailbox"),
    ("I clicked a phishing link and got a suspicious sign-in alert", "security-incident"),
    ("checkout API returning 503 errors for all customers", "major-incident"),
])
def test_search_finds_the_right_article(query, expected):
    results = default_kb().search(query)
    assert results and results[0]["article"] == expected


def test_search_returns_nothing_for_unrelated_query():
    assert default_kb().search("zzz qqq") == []


def test_every_article_has_metadata():
    for a in default_kb().articles:
        assert a.title and a.category and a.team and a.body
