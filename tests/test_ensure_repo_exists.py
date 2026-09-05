import time

import service


class _FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


class TestEnsureRepoExistsAlreadyPresent:
    def test_returns_true_when_repo_found(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/my-repo")
        monkeypatch.setattr(service.requests, "get", lambda *a, **kw: _FakeResponse(200))
        assert service.ensure_repo_exists() is True

    def test_queries_expected_api_url_and_auth(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/my-repo.git")
        captured = {}

        def fake_get(url, auth=None, timeout=None):
            captured["url"] = url
            captured["auth"] = auth
            return _FakeResponse(200)

        monkeypatch.setattr(service.requests, "get", fake_get)
        service.ensure_repo_exists()
        assert captured["url"] == "https://api.github.com/repos/alice/my-repo"
        assert captured["auth"] == ("alice", "tok")

    def test_strips_trailing_slash_from_repo_url(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/my-repo/")
        captured = {}

        def fake_get(url, auth=None, timeout=None):
            captured["url"] = url
            return _FakeResponse(200)

        monkeypatch.setattr(service.requests, "get", fake_get)
        service.ensure_repo_exists()
        assert captured["url"].endswith("/repos/alice/my-repo")

    def test_empty_repo_url_produces_empty_repo_name(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="")
        captured = {}

        def fake_get(url, auth=None, timeout=None):
            captured["url"] = url
            return _FakeResponse(200)

        monkeypatch.setattr(service.requests, "get", fake_get)
        service.ensure_repo_exists()
        assert captured["url"] == "https://api.github.com/repos/alice/"


class TestEnsureRepoExistsMissing:
    def test_creates_repo_and_returns_true_on_success(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/new-repo")
        monkeypatch.setattr(service.requests, "get", lambda *a, **kw: _FakeResponse(404))
        monkeypatch.setattr(service.requests, "post", lambda *a, **kw: _FakeResponse(201))
        monkeypatch.setattr(service.time, "sleep", lambda s: None)
        assert service.ensure_repo_exists() is True

    def test_create_payload_uses_parsed_repo_name(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/new-repo.git")
        captured = {}

        def fake_post(url, auth=None, json=None, timeout=None):
            captured["url"] = url
            captured["payload"] = json
            return _FakeResponse(201)

        monkeypatch.setattr(service.requests, "get", lambda *a, **kw: _FakeResponse(404))
        monkeypatch.setattr(service.requests, "post", fake_post)
        monkeypatch.setattr(service.time, "sleep", lambda s: None)
        service.ensure_repo_exists()
        assert captured["url"] == "https://api.github.com/user/repos"
        assert captured["payload"]["name"] == "new-repo"
        assert captured["payload"]["private"] is True
        assert captured["payload"]["auto_init"] is True

    def test_waits_after_successful_creation(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/new-repo")
        sleep_calls = []
        monkeypatch.setattr(service.requests, "get", lambda *a, **kw: _FakeResponse(404))
        monkeypatch.setattr(service.requests, "post", lambda *a, **kw: _FakeResponse(201))
        monkeypatch.setattr(service.time, "sleep", lambda s: sleep_calls.append(s))
        service.ensure_repo_exists()
        assert sleep_calls == [5]

    def test_returns_false_when_creation_fails(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/new-repo")
        monkeypatch.setattr(service.requests, "get", lambda *a, **kw: _FakeResponse(404))
        monkeypatch.setattr(service.requests, "post", lambda *a, **kw: _FakeResponse(422, "validation failed"))
        assert service.ensure_repo_exists() is False


class TestEnsureRepoExistsOtherOutcomes:
    def test_returns_false_on_unexpected_status_code(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/my-repo")
        monkeypatch.setattr(service.requests, "get", lambda *a, **kw: _FakeResponse(500))
        assert service.ensure_repo_exists() is False

    def test_returns_false_when_get_raises(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/my-repo")

        def raise_connection_error(*a, **kw):
            raise service.requests.exceptions.ConnectionError("no network")

        monkeypatch.setattr(service.requests, "get", raise_connection_error)
        assert service.ensure_repo_exists() is False

    def test_returns_false_and_logs_when_get_raises(self, monkeypatch, env_vars, caplog):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/my-repo")

        def raise_error(*a, **kw):
            raise RuntimeError("boom")

        monkeypatch.setattr(service.requests, "get", raise_error)
        with caplog.at_level("ERROR"):
            result = service.ensure_repo_exists()
        assert result is False
        assert any("Error checking/creating repo" in record.message for record in caplog.records)
