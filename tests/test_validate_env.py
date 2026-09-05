import pytest

import service


class TestValidateEnvMissingFile:
    def test_copies_template_and_returns_false(self, isolated_cwd):
        (isolated_cwd / ".env.example").write_text("GITHUB_USERNAME=your_username\n")
        result = service.validate_env()
        assert result is False
        env_file = isolated_cwd / ".env"
        assert env_file.exists()
        assert env_file.read_text() == (isolated_cwd / ".env.example").read_text()

    def test_logs_warning_when_template_is_copied(self, isolated_cwd, caplog):
        (isolated_cwd / ".env.example").write_text("GITHUB_USERNAME=your_username\n")
        with caplog.at_level("WARNING"):
            service.validate_env()
        assert any(".env not found" in record.message for record in caplog.records)

    def test_raises_if_template_is_also_missing(self, isolated_cwd):
        # There is no try/except around shutil.copy, so a missing template
        # propagates as a plain FileNotFoundError rather than being handled.
        with pytest.raises(FileNotFoundError):
            service.validate_env()


class TestValidateEnvExistingFile:
    def test_returns_false_when_default_username_still_present(self, isolated_cwd, monkeypatch, env_vars):
        (isolated_cwd / ".env").write_text("GITHUB_USERNAME=your_username\n")
        monkeypatch.setattr(service, "load_dotenv", lambda path: None)
        env_vars(GITHUB_USERNAME="your_username")
        assert service.validate_env() is False

    def test_logs_warning_when_default_username_still_present(self, isolated_cwd, monkeypatch, env_vars, caplog):
        (isolated_cwd / ".env").write_text("GITHUB_USERNAME=your_username\n")
        monkeypatch.setattr(service, "load_dotenv", lambda path: None)
        env_vars(GITHUB_USERNAME="your_username")
        with caplog.at_level("WARNING"):
            service.validate_env()
        assert any("PLEASE UPDATE YOUR .env FILE" in record.message for record in caplog.records)

    def test_returns_true_when_username_customized(self, isolated_cwd, monkeypatch, env_vars):
        (isolated_cwd / ".env").write_text("GITHUB_USERNAME=realuser\n")
        monkeypatch.setattr(service, "load_dotenv", lambda path: None)
        env_vars(GITHUB_USERNAME="realuser")
        assert service.validate_env() is True

    def test_returns_true_when_username_env_var_unset(self, isolated_cwd, monkeypatch):
        # GITHUB_USERNAME missing entirely is not equal to "your_username",
        # so this is treated the same as a customized value.
        (isolated_cwd / ".env").write_text("")
        monkeypatch.setattr(service, "load_dotenv", lambda path: None)
        monkeypatch.delenv("GITHUB_USERNAME", raising=False)
        assert service.validate_env() is True

    def test_calls_load_dotenv_with_env_path(self, isolated_cwd, monkeypatch, env_vars):
        (isolated_cwd / ".env").write_text("GITHUB_USERNAME=realuser\n")
        captured = {}
        monkeypatch.setattr(service, "load_dotenv", lambda path: captured.setdefault("path", path))
        env_vars(GITHUB_USERNAME="realuser")
        service.validate_env()
        assert captured["path"] == service.ENV_PATH

    def test_does_not_copy_template_when_env_already_exists(self, isolated_cwd, monkeypatch, env_vars):
        (isolated_cwd / ".env").write_text("GITHUB_USERNAME=realuser\n")
        # No .env.example present; if validate_env tried to copy it, this
        # would raise. Its absence here proves the copy branch was skipped.
        monkeypatch.setattr(service, "load_dotenv", lambda path: None)
        env_vars(GITHUB_USERNAME="realuser")
        assert service.validate_env() is True
