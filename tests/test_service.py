"""Tests for optional user-service installation."""

from pathlib import Path

from people_context import service


def test_unit_text_uses_current_python_and_pins_database(tmp_path: Path) -> None:
    text = service._unit_text(
        executable="/opt/people context/bin/python",
        db_path=tmp_path / "people db.sqlite3",
        host="127.0.0.1",
        port=8765,
    )

    assert "ExecStart='/opt/people context/bin/python' -m people_context.adapters.mcp.server" in text
    assert "--http --host 127.0.0.1 --port 8765" in text
    assert "--db '" + str(tmp_path / "people db.sqlite3") + "'" in text
    assert "Restart=on-failure" in text


def test_install_service_writes_unit_and_enables_it(tmp_path: Path, monkeypatch) -> None:
    calls: list[tuple[str, ...]] = []
    monkeypatch.setattr(service.sys, "platform", "linux")
    monkeypatch.setattr(service.sys, "executable", "/python")
    monkeypatch.setattr(service, "_systemd_user_dir", lambda: tmp_path)
    monkeypatch.setattr(service.shutil, "which", lambda name: "/usr/bin/systemctl")
    monkeypatch.setattr(service, "_systemctl", lambda *args: calls.append(args))

    unit_path = service.install_service(db_path=tmp_path / "people.db")

    assert unit_path == tmp_path / service.SERVICE_NAME
    assert unit_path.exists()
    assert "--db /" in unit_path.read_text(encoding="utf-8")
    assert calls == [
        ("daemon-reload",),
        ("enable", "--now", service.SERVICE_NAME),
        ("restart", service.SERVICE_NAME),
    ]
