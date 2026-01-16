from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from boring.cli.model import app

runner = CliRunner()


def test_model_list():
    with patch("boring.llm.local_llm.list_available_models") as mock_list:
        mock_list.return_value = [
            {"name": "test-model.gguf", "size_mb": 100.0, "path": "/tmp/models/test-model.gguf"}
        ]

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "test-model.gguf" in result.stdout
        assert "100.0" in result.stdout


def test_model_download():
    # Mock download_model
    with patch("boring.llm.local_llm.download_model") as mock_download:
        mock_download.return_value = "/tmp/models/qwen2.5.gguf"

        # Test unknown model
        result = runner.invoke(app, ["download", "unknown-model"])
        assert result.exit_code != 0
        assert "Unknown model ID" in result.stdout

        # Test valid model (we use a key that exists in RECOMMENDED_MODELS)
        # We need to ensure RECOMMENDED_MODELS has 'qwen2.5-1.5b' or similar
        # Or patch RECOMMENDED_MODELS

        with patch(
            "boring.llm.local_llm.RECOMMENDED_MODELS",
            {
                "test-model": {
                    "url": "http://foo/bar.gguf",
                    "size_mb": 100,
                    "context": 2048,
                    "description": "Test",
                }
            },
        ):
            result = runner.invoke(app, ["download", "test-model"])
            assert result.exit_code == 0
            assert "Successfully downloaded" in result.stdout


def test_model_delete():
    with patch("boring.llm.local_llm.get_model_dir") as mock_dir:
        mock_path = MagicMock()
        mock_dir.return_value = mock_path

        # Case: Model dir not exists
        mock_path.exists.return_value = False
        result = runner.invoke(app, ["delete", "foo"])
        assert "Model directory does not exist" in result.stdout

        # Case: Model dir exists, file deletion
        mock_path.exists.return_value = True
        mock_file = MagicMock()
        mock_file.name = "test-model.gguf"
        mock_path.glob.return_value = [mock_file]

        # Force delete
        result = runner.invoke(app, ["delete", "test-model", "--force"])
        assert "Deleted test-model.gguf" in result.stdout
        mock_file.unlink.assert_called_once()
