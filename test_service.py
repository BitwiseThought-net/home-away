import unittest
import json
from unittest.mock import patch, MagicMock, mock_open
import service

class TestIPTracker(unittest.TestCase):

    @patch('requests.get')
    def test_get_external_ip_success(self, mock_get):
        mock_get.return_value.text = "123.123.123.123"
        mock_get.return_value.status_code = 200
        ip = service.get_external_ip()
        self.assertEqual(ip, "123.123.123.123")

    @patch('os.path.exists')
    @patch('shutil.copy')
    def test_validate_env_missing_file(self, mock_copy, mock_exists):
        mock_exists.return_value = False
        result = service.validate_env()
        self.assertFalse(result)
        mock_copy.assert_called_with(".env.example", ".env")

    @patch('service.load_dotenv')
    @patch('os.getenv')
    @patch('os.path.exists')
    def test_validate_env_with_defaults(self, mock_exists, mock_getenv, _mock_load):
        mock_exists.return_value = True
        mock_getenv.side_effect = lambda k, default=None: "your_username" if k == "GITHUB_USERNAME" else "other"
        result = service.validate_env()
        self.assertFalse(result)

    @patch('service.Repo.clone_from')
    @patch('os.getenv')
    @patch('os.path.exists')
    @patch('shutil.rmtree')
    def test_push_to_github_json_structure(self, _mock_rm, mock_exists, mock_getenv, mock_clone):
        env_vars = {
            "GITHUB_USERNAME": "test_user",
            "GITHUB_PASSWORD": "test_password",
            "GITHUB_REPO_URL": "https://github.com",
            "IP_LOG_FILE": "ip_log.json"
        }
        mock_getenv.side_effect = lambda k, default=None: env_vars.get(k, default)
        mock_exists.return_value = True
        mock_repo = MagicMock()
        mock_clone.return_value = mock_repo

        with patch("builtins.open", mock_open()) as mocked_file:
            service.push_to_github("1.2.3.4")
            written_data = "".join(call.args for call in mocked_file().write.call_args_list)
            data = json.loads(written_data)
            self.assertEqual(data["IP"], "1.2.3.4")
            self.assertIn("Last_Modified", data)

    @patch('requests.get')
    @patch('os.getenv')
    def test_ensure_repo_exists_already_there(self, mock_getenv, mock_requests_get):
        """Test that ensure_repo_exists returns True if repo is found."""
        mock_getenv.side_effect = lambda k, default=None: "test_val"
        mock_requests_get.return_value.status_code = 200
        result = service.ensure_repo_exists()
        self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()
