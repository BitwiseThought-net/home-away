"""
push_to_github() clones a repo with GitPython, writes a JSON log file into
it, and commits/pushes. Tests mock service.Repo.clone_from (never touching
the network or filesystem for a real clone) and builtins.open (via
mock_open) to capture what would have been written, following the same
approach as update_hosts_file's tests.
"""
import json
from unittest.mock import MagicMock, mock_open, patch

import service


def _patch_tmp_dir_exists(monkeypatch, exists=False):
    real_exists = service.os.path.exists

    def fake_exists(path):
        if path == "/tmp/repo_sync":
            return exists
        return real_exists(path)

    monkeypatch.setattr(service.os.path, "exists", fake_exists)


class TestPushToGithub:
    def test_writes_expected_json_payload(self, monkeypatch, env_vars):
        env_vars(
            GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok",
            GITHUB_REPO_URL="https://github.com/alice/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, exists=False)
        mock_repo = MagicMock()
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: mock_repo)

        m = mock_open()
        with patch("builtins.open", m):
            service.push_to_github("1.2.3.4")

        written = "".join(call.args[0] for call in m().write.call_args_list)
        data = json.loads(written)
        assert data["IP"] == "1.2.3.4"
        assert "Last_Modified" in data

    def test_clones_with_credentials_embedded_in_url(self, monkeypatch, env_vars):
        env_vars(
            GITHUB_USERNAME="alice", GITHUB_PASSWORD="s3cr3t",
            GITHUB_REPO_URL="https://github.com/alice/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, exists=False)
        captured = {}

        def fake_clone(url, path):
            captured["url"] = url
            captured["path"] = path
            return MagicMock()

        monkeypatch.setattr(service.Repo, "clone_from", fake_clone)
        with patch("builtins.open", mock_open()):
            service.push_to_github("1.2.3.4")

        assert captured["url"] == "https://alice:s3cr3t@github.com/alice/repo"
        assert captured["path"] == "/tmp/repo_sync"

    def test_commits_and_pushes(self, monkeypatch, env_vars):
        env_vars(
            GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok",
            GITHUB_REPO_URL="https://github.com/alice/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, exists=False)
        mock_repo = MagicMock()
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: mock_repo)

        with patch("builtins.open", mock_open()):
            service.push_to_github("1.2.3.4")

        mock_repo.index.add.assert_called_once_with(["ip.json"])
        mock_repo.index.commit.assert_called_once()
        assert "1.2.3.4" in mock_repo.index.commit.call_args[0][0]
        mock_repo.remotes.origin.push.assert_called_once()

    def test_removes_stale_tmp_dir_before_cloning(self, monkeypatch, env_vars):
        env_vars(
            GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok",
            GITHUB_REPO_URL="https://github.com/alice/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, exists=True)
        rmtree_calls = []
        monkeypatch.setattr(service.shutil, "rmtree", lambda path: rmtree_calls.append(path))
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: MagicMock())

        with patch("builtins.open", mock_open()):
            service.push_to_github("1.2.3.4")

        assert rmtree_calls == ["/tmp/repo_sync"]

    def test_uses_default_log_filename_when_unset(self, monkeypatch, env_vars):
        env_vars(GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok", GITHUB_REPO_URL="https://github.com/alice/repo")
        monkeypatch.delenv("IP_LOG_FILE", raising=False)
        _patch_tmp_dir_exists(monkeypatch, exists=False)
        mock_repo = MagicMock()
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: mock_repo)

        with patch("builtins.open", mock_open()):
            service.push_to_github("1.2.3.4")

        mock_repo.index.add.assert_called_once_with(["external_ip.json"])

    def test_logs_info_on_successful_push(self, monkeypatch, env_vars, caplog):
        env_vars(
            GITHUB_USERNAME="alice", GITHUB_PASSWORD="tok",
            GITHUB_REPO_URL="https://github.com/alice/repo", IP_LOG_FILE="ip.json",
        )
        _patch_tmp_dir_exists(monkeypatch, exists=False)
        monkeypatch.setattr(service.Repo, "clone_from", lambda url, path: MagicMock())

        with patch("builtins.open", mock_open()), caplog.at_level("INFO"):
            service.push_to_github("1.2.3.4")

        assert any("Pushed new IP to GitHub" in record.message for record in caplog.records)
