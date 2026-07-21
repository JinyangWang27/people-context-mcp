"""Install and manage an optional user-level HTTP backend service."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

SERVICE_NAME = "people-context.service"


def _systemd_user_dir() -> Path:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser()
    return config_home / "systemd" / "user"


def _unit_text(*, executable: str, db_path: Path, host: str, port: int) -> str:
    command = shlex.join(
        [
            executable,
            "-m",
            "people_context.adapters.mcp.server",
            "--http",
            "--host",
            host,
            "--port",
            str(port),
            "--db",
            str(db_path),
        ]
    )
    return f"""[Unit]
Description=people-context MCP HTTP backend
After=default.target

[Service]
Type=simple
ExecStart={command}
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
"""


def _systemctl(*args: str) -> None:
    if shutil.which("systemctl") is None:
        raise RuntimeError("systemctl is required to manage the user service")
    try:
        subprocess.run(["systemctl", "--user", *args], check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"systemctl --user {' '.join(args)} failed with exit code {exc.returncode}") from exc


def install_service(*, db_path: Path, host: str = "127.0.0.1", port: int = 8765) -> Path:
    """Install and start the backend as a systemd user service."""
    if not sys.platform.startswith("linux"):
        raise RuntimeError("automatic service installation currently supports Linux systemd only")
    if host != "127.0.0.1":
        raise ValueError("the people-context HTTP backend must remain loopback-only")
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")

    unit_dir = _systemd_user_dir()
    unit_dir.mkdir(parents=True, exist_ok=True)
    unit_path = unit_dir / SERVICE_NAME
    unit_path.write_text(
        _unit_text(executable=sys.executable, db_path=db_path, host=host, port=port),
        encoding="utf-8",
    )
    _systemctl("daemon-reload")
    _systemctl("enable", "--now", SERVICE_NAME)
    _systemctl("restart", SERVICE_NAME)
    return unit_path


def uninstall_service() -> None:
    """Stop, disable, and remove the systemd user service."""
    if not sys.platform.startswith("linux"):
        raise RuntimeError("automatic service management currently supports Linux systemd only")
    _systemctl("disable", "--now", SERVICE_NAME)
    unit_path = _systemd_user_dir() / SERVICE_NAME
    unit_path.unlink(missing_ok=True)
    _systemctl("daemon-reload")


def service_status() -> int:
    """Return and display the systemd user service status."""
    if not sys.platform.startswith("linux"):
        raise RuntimeError("automatic service management currently supports Linux systemd only")
    completed = subprocess.run(["systemctl", "--user", "--no-pager", "status", SERVICE_NAME], check=False)
    return completed.returncode
