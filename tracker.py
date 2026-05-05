import unittest
import json
from unittest.mock import patch, MagicMock, mock_open
import tracker

class TestIPTracker(unittest.TestCase):

    @patch('tracker.requests.get')
    def test_get_external_ip_success(self, mock_get):
        mock_get.return_value.text = "123.123.123.123"
        mock_get.return_value.status_code = 200
        ip = tracker.get_external_ip()
        self.assertEqual(ip, "123.123.123.123")

    @patch('tracker.os.path.exists')
    @patch('tracker.shutil.copy')
    def test_validate_env_missing_file(self, mock_copy, mock_exists):
        mock_exists.return_value = False
        result = tracker.validate_env()
        self.assertFalse(result)
        mock_copy.assert_called_with(".env.example", ".env")

    @patch('tracker.load_dotenv')
    @patch('tracker.os.getenv')
    @patch('tracker.os.path.exists')
    def test_validate_env_with_defaults(self, mock_exists, mock_getenv, _mock_load):
        mock_exists.return_value = True
        mock_getenv.side_effect = lambda k: "your_username" if k == "GITHUB_USERNAME" else "other"
        result = tracker.validate_env()
        self.assertFalse(result)

    @patch('tracker.Repo.clone_from')
    @patch('tracker.os.getenv')
    @patch('tracker.os.path.exists')
    @patch('tracker.shutil.rmtree')
    def test_push_to_github_json_structure(self, _mock_rm, mock_exists, mock_getenv, mock_clone):
        env_vars = {
            "GITHUB_USERNAME": "test_user",
            "GITHUB_PASSWORD": "test_password",
            "GITHUB_REPO_URL": "https://github.com",
            "IP_LOG_FILE": "ip_log.json"
        }
        mock_getenv.side_effect = env_vars.get
        mock_exists.return_value = True
        mock_repo = MagicMock()
        mock_clone.return_value = mock_repo
        
        with patch("builtins.open", mock_open()) as mocked_file:
            tracker.push_to_github("1.2.3.4")
            written_data = "".join(call.args[0] for call in mocked_file().write.call_args_list)
            data = json.loads(written_data)
            self.assertEqual(data["IP"], "1.2.3.4")

if __name__ == "__main__":
    unittest.main()
