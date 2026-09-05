"""
main() is a `while True:` loop that only ever exits via an unhandled
exception (there's no break/return in it at all). To test its per-iteration
behavior we mock time.sleep to raise a sentinel exception after a chosen
number of calls, run main() inside pytest.raises(_StopLoop), and then
assert on what happened during the iteration(s) that ran.
"""
import pytest

import service


class _StopLoop(Exception):
    """Raised from a mocked time.sleep to escape service.main()'s loop."""


def _stop_after(n):
    """Returns a time.sleep replacement that raises _StopLoop on the nth call."""
    calls = {"n": 0}

    def _sleep(seconds):
        calls["n"] += 1
        if calls["n"] >= n:
            raise _StopLoop()

    return _sleep, calls


class TestMainServerMode:
    def test_pushes_new_ip_when_found(self, monkeypatch, env_vars):
        env_vars(CLIENT="false")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "get_external_ip", lambda: "1.2.3.4")
        push_calls = []
        monkeypatch.setattr(service, "push_to_github", lambda ip: push_calls.append(ip))
        sleep_fn, _ = _stop_after(1)
        monkeypatch.setattr(service.time, "sleep", sleep_fn)

        with pytest.raises(_StopLoop):
            service.main()

        assert push_calls == ["1.2.3.4"]

    def test_skips_push_when_no_ip_found(self, monkeypatch, env_vars):
        env_vars(CLIENT="false")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "get_external_ip", lambda: None)
        push_calls = []
        monkeypatch.setattr(service, "push_to_github", lambda ip: push_calls.append(ip))
        sleep_fn, _ = _stop_after(1)
        monkeypatch.setattr(service.time, "sleep", sleep_fn)

        with pytest.raises(_StopLoop):
            service.main()

        assert push_calls == []

    def test_does_not_repush_the_same_ip_on_next_iteration(self, monkeypatch, env_vars):
        env_vars(CLIENT="false")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "get_external_ip", lambda: "1.2.3.4")
        push_calls = []
        monkeypatch.setattr(service, "push_to_github", lambda ip: push_calls.append(ip))
        sleep_fn, _ = _stop_after(2)  # let two iterations run
        monkeypatch.setattr(service.time, "sleep", sleep_fn)

        with pytest.raises(_StopLoop):
            service.main()

        assert push_calls == ["1.2.3.4"]

    def test_pushes_again_when_ip_changes(self, monkeypatch, env_vars):
        env_vars(CLIENT="false")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        ips = iter(["1.1.1.1", "2.2.2.2"])
        monkeypatch.setattr(service, "get_external_ip", lambda: next(ips))
        push_calls = []
        monkeypatch.setattr(service, "push_to_github", lambda ip: push_calls.append(ip))
        sleep_fn, _ = _stop_after(2)
        monkeypatch.setattr(service.time, "sleep", sleep_fn)

        with pytest.raises(_StopLoop):
            service.main()

        assert push_calls == ["1.1.1.1", "2.2.2.2"]


class TestMainClientMode:
    def test_updates_hosts_file_when_ip_present(self, monkeypatch, env_vars):
        env_vars(CLIENT="true", HOME_HOSTNAME="home.example.com")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "pull_from_github", lambda: {"IP": "5.6.7.8"})
        update_calls = []
        monkeypatch.setattr(service, "update_hosts_file", lambda ip, host: update_calls.append((ip, host)))
        sleep_fn, _ = _stop_after(1)
        monkeypatch.setattr(service.time, "sleep", sleep_fn)

        with pytest.raises(_StopLoop):
            service.main()

        assert update_calls == [("5.6.7.8", "home.example.com")]

    def test_skips_update_when_no_data_returned(self, monkeypatch, env_vars):
        env_vars(CLIENT="true")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "pull_from_github", lambda: None)
        update_calls = []
        monkeypatch.setattr(service, "update_hosts_file", lambda ip, host: update_calls.append((ip, host)))
        sleep_fn, _ = _stop_after(1)
        monkeypatch.setattr(service.time, "sleep", sleep_fn)

        with pytest.raises(_StopLoop):
            service.main()

        assert update_calls == []

    def test_skips_update_when_data_has_no_ip_key(self, monkeypatch, env_vars):
        env_vars(CLIENT="true")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "pull_from_github", lambda: {"Last_Modified": "x"})
        update_calls = []
        monkeypatch.setattr(service, "update_hosts_file", lambda ip, host: update_calls.append((ip, host)))
        sleep_fn, _ = _stop_after(1)
        monkeypatch.setattr(service.time, "sleep", sleep_fn)

        with pytest.raises(_StopLoop):
            service.main()

        assert update_calls == []

    def test_client_flag_is_case_insensitive(self, monkeypatch, env_vars):
        env_vars(CLIENT="TRUE", HOME_HOSTNAME="home.example.com")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "pull_from_github", lambda: {"IP": "5.6.7.8"})
        update_calls = []
        monkeypatch.setattr(service, "update_hosts_file", lambda ip, host: update_calls.append((ip, host)))
        sleep_fn, _ = _stop_after(1)
        monkeypatch.setattr(service.time, "sleep", sleep_fn)

        with pytest.raises(_StopLoop):
            service.main()

        assert update_calls == [("5.6.7.8", "home.example.com")]


class TestMainIntervalHandling:
    def test_uses_configured_interval(self, monkeypatch, env_vars):
        env_vars(CLIENT="false", CHECK_INTERVAL_SEC="42")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "get_external_ip", lambda: None)
        sleep_calls = []

        def sleep_fn(s):
            sleep_calls.append(s)
            raise _StopLoop()

        monkeypatch.setattr(service.time, "sleep", sleep_fn)
        with pytest.raises(_StopLoop):
            service.main()
        assert sleep_calls == [42]

    def test_invalid_interval_falls_back_to_300(self, monkeypatch, env_vars):
        env_vars(CLIENT="false", CHECK_INTERVAL_SEC="not-a-number")
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "get_external_ip", lambda: None)
        sleep_calls = []

        def sleep_fn(s):
            sleep_calls.append(s)
            raise _StopLoop()

        monkeypatch.setattr(service.time, "sleep", sleep_fn)
        with pytest.raises(_StopLoop):
            service.main()
        assert sleep_calls == [300]

    def test_missing_interval_env_var_defaults_to_300(self, monkeypatch, env_vars):
        env_vars(CLIENT="false")
        monkeypatch.delenv("CHECK_INTERVAL_SEC", raising=False)
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: True)
        monkeypatch.setattr(service, "get_external_ip", lambda: None)
        sleep_calls = []

        def sleep_fn(s):
            sleep_calls.append(s)
            raise _StopLoop()

        monkeypatch.setattr(service.time, "sleep", sleep_fn)
        with pytest.raises(_StopLoop):
            service.main()
        assert sleep_calls == [300]


class TestMainInvalidEnvironment:
    def test_sleeps_60s_and_skips_repo_check(self, monkeypatch):
        monkeypatch.setattr(service, "validate_env", lambda: False)
        repo_check_calls = []
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: repo_check_calls.append(1) or True)
        sleep_calls = []

        def sleep_fn(s):
            sleep_calls.append(s)
            raise _StopLoop()

        monkeypatch.setattr(service.time, "sleep", sleep_fn)
        with pytest.raises(_StopLoop):
            service.main()

        assert sleep_calls == [60]
        # Python's `and` short-circuits, so ensure_repo_exists is never
        # even called when validate_env() is False.
        assert repo_check_calls == []

    def test_sleeps_60s_when_repo_check_fails(self, monkeypatch):
        monkeypatch.setattr(service, "validate_env", lambda: True)
        monkeypatch.setattr(service, "ensure_repo_exists", lambda: False)
        sleep_calls = []

        def sleep_fn(s):
            sleep_calls.append(s)
            raise _StopLoop()

        monkeypatch.setattr(service.time, "sleep", sleep_fn)
        with pytest.raises(_StopLoop):
            service.main()

        assert sleep_calls == [60]


class TestMainStartup:
    def test_logs_startup_message_with_os_info(self, monkeypatch, caplog):
        monkeypatch.setattr(service, "validate_env", lambda: False)

        def sleep_fn(s):
            raise _StopLoop()

        monkeypatch.setattr(service.time, "sleep", sleep_fn)
        with caplog.at_level("INFO"):
            with pytest.raises(_StopLoop):
                service.main()

        assert any("Starting Service" in record.message for record in caplog.records)
