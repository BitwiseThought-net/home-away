"""
update_hosts_file() reads/writes a hardcoded path ("/app/hosts_mount")
rather than accepting one as a parameter, so tests patch os.path.exists
(scoped to that one path, real filesystem behavior otherwise) and
builtins.open (via unittest.mock.mock_open) to intercept the read/write
without touching any real file.
"""
from unittest.mock import mock_open, patch

import service


def _patch_hosts_path_exists(monkeypatch, exists=True):
    real_exists = service.os.path.exists

    def fake_exists(path):
        if path == "/app/hosts_mount":
            return exists
        return real_exists(path)

    monkeypatch.setattr(service.os.path, "exists", fake_exists)


class TestUpdateHostsFileMountMissing:
    def test_logs_error_and_returns_without_opening_file(self, monkeypatch, caplog):
        _patch_hosts_path_exists(monkeypatch, exists=False)
        with caplog.at_level("ERROR"):
            service.update_hosts_file("1.2.3.4", "home.example.com")
        assert any("Hosts mount not found" in record.message for record in caplog.records)


class TestUpdateHostsFileReplacesExistingLine:
    def test_replaces_matching_hostname_line(self, monkeypatch):
        _patch_hosts_path_exists(monkeypatch, exists=True)
        initial = "127.0.0.1 localhost\n1.1.1.1 home.example.com\n"
        m = mock_open(read_data=initial)
        with patch("builtins.open", m):
            service.update_hosts_file("2.2.2.2", "home.example.com")
        written = "".join(m().writelines.call_args[0][0])
        assert "2.2.2.2 home.example.com" in written
        assert "1.1.1.1 home.example.com" not in written
        assert "127.0.0.1 localhost" in written

    def test_only_touches_the_matching_hostname(self, monkeypatch):
        _patch_hosts_path_exists(monkeypatch, exists=True)
        initial = "1.1.1.1 other.example.com\n1.1.1.1 home.example.com\n"
        m = mock_open(read_data=initial)
        with patch("builtins.open", m):
            service.update_hosts_file("2.2.2.2", "home.example.com")
        written = "".join(m().writelines.call_args[0][0])
        assert "1.1.1.1 other.example.com" in written
        assert "2.2.2.2 home.example.com" in written


class TestUpdateHostsFileAppendsNewLine:
    def test_appends_when_hostname_not_present(self, monkeypatch):
        _patch_hosts_path_exists(monkeypatch, exists=True)
        initial = "127.0.0.1 localhost\n"
        m = mock_open(read_data=initial)
        with patch("builtins.open", m):
            service.update_hosts_file("3.3.3.3", "new-host.example.com")
        written_lines = m().writelines.call_args[0][0]
        assert written_lines[-1] == "3.3.3.3 new-host.example.com\n"
        assert "127.0.0.1 localhost\n" in written_lines


class TestUpdateHostsFileLogsSuccess:
    def test_logs_info_on_successful_update(self, monkeypatch, caplog):
        _patch_hosts_path_exists(monkeypatch, exists=True)
        m = mock_open(read_data="127.0.0.1 localhost\n")
        with patch("builtins.open", m), caplog.at_level("INFO"):
            service.update_hosts_file("4.4.4.4", "home.example.com")
        assert any("Updated hosts" in record.message for record in caplog.records)


class TestUpdateHostsFileHandlesWriteErrors:
    def test_open_failure_is_caught_and_logged(self, monkeypatch, caplog):
        _patch_hosts_path_exists(monkeypatch, exists=True)

        def boom(*args, **kwargs):
            raise PermissionError("no permission")

        with patch("builtins.open", boom), caplog.at_level("ERROR"):
            service.update_hosts_file("5.5.5.5", "home.example.com")
        assert any("Failed to update hosts file" in record.message for record in caplog.records)
