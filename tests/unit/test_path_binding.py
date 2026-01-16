def test_dashboard_paths_use_settings_root(tmp_path, monkeypatch):
    from boring.cli import dashboard
    from boring.core.config import settings

    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path, raising=False)
    paths = dashboard._get_dashboard_paths()

    assert paths["project_root"] == tmp_path
    assert str(paths["status_file"]).startswith(str(tmp_path))
    assert paths["log_file"].parent == tmp_path / "logs"


def test_dashboard_tui_paths_use_settings_root(tmp_path, monkeypatch):
    from boring.cli import dashboard_tui
    from boring.core.config import settings

    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path, raising=False)
    paths = dashboard_tui._get_paths()

    assert str(paths["status_file"]).startswith(str(tmp_path))
    assert paths["log_file"].parent == tmp_path / "logs"


def test_monitor_paths_use_settings_root(tmp_path, monkeypatch):
    from boring.core.config import settings
    from boring.services import monitor

    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path, raising=False)
    paths = monitor._get_paths()

    assert paths["status_file"] == tmp_path / settings.STATUS_FILE
    assert paths["log_file"].parent == tmp_path / "logs"
