import typer

from boring.cli.doctor import check
from boring.core.config import settings


def test_doctor_check(tmp_path, monkeypatch, capsys):
    """Test standard doctor check (health)."""
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    (tmp_path / ".boring").mkdir()

    try:
        check(generate_context=False)
    except typer.Exit as e:
        assert e.exit_code == 0 or e.exit_code == 1

    captured = capsys.readouterr()
    assert "Health Score" in captured.out


def test_doctor_generate_context(tmp_path, monkeypatch, capsys):
    """Test context generation."""
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)

    # Setup dummy project
    (tmp_path / ".boring").mkdir()
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "test.py").touch()

    try:
        check(generate_context=True)
    except typer.Exit:
        pass

    captured = capsys.readouterr()
    assert "Generated GEMINI.md" in captured.out

    ctx_file = tmp_path / "GEMINI.md"
    assert ctx_file.exists()
    content = ctx_file.read_text("utf-8")
    assert "Project Context" in content
