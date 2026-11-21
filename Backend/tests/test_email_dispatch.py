import pytest
from utils.email import _dispatch_email


def test_dispatch_email_default_goes_to_provider(monkeypatch):
    """When USE_LOCAL_EMAIL is unset, dispatch goes to the real provider path."""
    monkeypatch.delenv("USE_LOCAL_EMAIL", raising=False)
    monkeypatch.setenv("BREVO_API_KEY", "mock-brevo-key")

    called = []

    def mock_brevo(to_email, subject, html_content, plain_text):
        called.append((to_email, subject))
        return True

    monkeypatch.setattr("utils.email._send_via_brevo", mock_brevo)

    success = _dispatch_email("user@example.com", "Test Subject", "<p>Hello</p>", "Hello")
    assert success is True
    assert len(called) == 1
    assert called[0] == ("user@example.com", "Test Subject")


def test_dispatch_email_local_mode_true(monkeypatch):
    """When USE_LOCAL_EMAIL is 'true', dispatch returns True immediately without calling providers."""
    monkeypatch.setenv("USE_LOCAL_EMAIL", "true")
    monkeypatch.setenv("BREVO_API_KEY", "mock-brevo-key")

    called = []

    def mock_brevo(to_email, subject, html_content, plain_text):
        called.append((to_email, subject))
        return True

    monkeypatch.setattr("utils.email._send_via_brevo", mock_brevo)

    success = _dispatch_email("user@example.com", "Test Subject", "<p>Hello</p>", "Hello")
    assert success is True
    assert len(called) == 0, "Provider must not be called when USE_LOCAL_EMAIL is true"


def test_dispatch_email_explicit_false_goes_to_provider(monkeypatch):
    """When USE_LOCAL_EMAIL is explicitly 'false', dispatch goes to real providers."""
    monkeypatch.setenv("USE_LOCAL_EMAIL", "false")
    monkeypatch.setenv("BREVO_API_KEY", "mock-brevo-key")

    called = []

    def mock_brevo(to_email, subject, html_content, plain_text):
        called.append((to_email, subject))
        return True

    monkeypatch.setattr("utils.email._send_via_brevo", mock_brevo)

    success = _dispatch_email("user@example.com", "Test Subject", "<p>Hello</p>", "Hello")
    assert success is True
    assert len(called) == 1
    assert called[0] == ("user@example.com", "Test Subject")
