from unittest.mock import MagicMock, mock_open, patch

import service


def _patch_tmp_dir_exists(monkeypatch, tmp_dir_exists=False, log_file_exists=True):
    real_exists = service.os.path.exists

    def fake_exists(path):
        if path == "/tmp/repo_pull":
            return tmp_dir_exists
        if path.startswith("/tmp/repo_pull/"):
            return log_file_exists
        return real_exists(path)

    monkeypatch.setattr(service.os.path, "exists", fake_exists)


class TestPullFromGithub:
    def test_returns_parsed_json_when_log_file_present(self, monkeypatch, env_vars):
        env_vars(
            GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok",
            GITHUB_REPO_URL="https://github.com/alice/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, tmp_dir_exists=False, log_file_exists=True)
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: MagicMock())

        m = mock_open(read_data='{"IP": "9.9.9.9", "Last_Modified": "2026-01-01 00:00:00"}')
        with patch("builtins.open", m):
            result = service.pull_from_github()

        assert result == {"IP": "9.9.9.9", "Last_Modified": "2026-01-01 00:00:00"}

    def test_returns_none_when_log_file_missing(self, monkeypatch, env_vars):
        env_vars(
            GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok",
            GITHUB_REPO_URL="https://github.com/alice/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, tmp_dir_exists=False, log_file_exists=False)
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: MagicMock())

        assert service.pull_from_github() is None

    def test_clones_with_credentials_embedded_in_url(self, monkeypatch, env_vars):
        env_vars(
            GITHUB_USERNAME="bob", GITHUB_PASSWORD="hunter2",
            GITHUB_REPO_URL="https://github.com/bob/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, tmp_dir_exists=False, log_file_exists=True)
        captured = {}

        def fake_clone(url, path):
            captured["url"] = url
            captured["path"] = path
            return MagicMock()

        monkeypatch.setattr(service.Repo, "clone_from", fake_clone)
        with patch("builtins.open", mock_open(read_data='{"IP": "1.1.1.1"}')):
            service.pull_from_github()

        assert captured["url"] == "https://bob:hunter2@github.com/bob/repo"
        assert captured["path"] == "/tmp/repo_pull"

    def test_removes_stale_tmp_dir_before_cloning(self, monkeypatch, env_vars):
        env_vars(
            GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok",
            GITHUB_REPO_URL="https://github.com/alice/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, tmp_dir_exists=True, log_file_exists=True)
        rmtree_calls = []
        monkeypatch.setattr(service.shutil, "rmtree", lambda path: rmtree_calls.append(path))
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: MagicMock())

        with patch("builtins.open", mock_open(read_data='{"IP": "1.1.1.1"}')):
            service.pull_from_github()

        assert rmtree_calls == ["/tmp/repo_pull"]

    def test_uses_default_log_filename_when_unset(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/repo")
        monkeypatch.delenv("IP_LOG_FILE", raising=False)
        checked_paths = []
        real_exists = service.os.path.exists

        def fake_exists(path):
            checked_paths.append(path)
            if path == "/tmp/repo_pull":
                return False
            if path.startswith("/tmp/repo_pull/"):
                return True
            return real_exists(path)

        monkeypatch.setattr(service.os.path, "exists", fake_exists)
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: MagicMock())

        with patch("builtins.open", mock_open(read_data='{"IP": "1.1.1.1"}')):
            service.pull_from_github()

        assert "/tmp/repo_pull/external_ip.json" in checked_paths
