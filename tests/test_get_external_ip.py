import service


class _FakeResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text


class TestGetExternalIp:
    def test_returns_ip_from_first_provider_on_success(self, monkeypatch):
        monkeypatch.setattr(service.requests, "get", lambda url, timeout=None: _FakeResponse(200, "  1.2.3.4  "))
        assert service.get_external_ip() == "1.2.3.4"

    def test_falls_back_to_second_provider_on_exception(self, monkeypatch):
        calls = []

        def fake_get(url, timeout=None):
            calls.append(url)
            if len(calls) == 1:
                raise service.requests.exceptions.Timeout("slow")
            return _FakeResponse(200, "9.9.9.9")

        monkeypatch.setattr(service.requests, "get", fake_get)
        assert service.get_external_ip() == "9.9.9.9"
        assert len(calls) == 2

    def test_falls_back_to_next_provider_on_non_200_status(self, monkeypatch):
        calls = []

        def fake_get(url, timeout=None):
            calls.append(url)
            if len(calls) == 1:
                return _FakeResponse(503)
            return _FakeResponse(200, "8.8.8.8")

        monkeypatch.setattr(service.requests, "get", fake_get)
        assert service.get_external_ip() == "8.8.8.8"

    def test_returns_none_when_all_providers_fail(self, monkeypatch):
        def always_fail(url, timeout=None):
            raise service.requests.exceptions.ConnectionError("down")

        monkeypatch.setattr(service.requests, "get", always_fail)
        assert service.get_external_ip() is None

    def test_logs_error_when_all_providers_fail(self, monkeypatch, caplog):
        monkeypatch.setattr(service.requests, "get", lambda url, timeout=None: _FakeResponse(500))
        with caplog.at_level("ERROR"):
            result = service.get_external_ip()
        assert result is None
        assert any("All IP check providers failed" in record.message for record in caplog.records)

    def test_tries_multiple_providers_before_giving_up(self, monkeypatch):
        seen_urls = []

        def fake_get(url, timeout=None):
            seen_urls.append(url)
            return _FakeResponse(500)

        monkeypatch.setattr(service.requests, "get", fake_get)
        service.get_external_ip()
        # All configured providers were attempted, and each is a distinct URL.
        assert len(seen_urls) >= 2
        assert len(set(seen_urls)) == len(seen_urls)
