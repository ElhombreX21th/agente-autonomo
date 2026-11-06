"""Isolated authenticated browser workflow: no persisted or printed credentials."""

import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

from agent_v3.identity import IdentityStore
from agent_v3.store import Store


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as directory:
        database = Path(directory) / "browser.sqlite3"
        _, token = IdentityStore(Store(database)).provision("Synthetic browser pilot")
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        environment = {
            **os.environ,
            "AGENT_DATABASE": str(database),
            "AGENT_AUTH_REQUIRED": "1",
            "AGENT_TEST_URL": base,
            "AGENT_TEST_CREDENTIAL": token,
        }
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "agent_v3.api:create_app",
                "--factory",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=root,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError("Browser test server exited during startup")
                try:
                    with opener.open(base + "/ready", timeout=1) as response:
                        if response.status == 200:
                            break
                except (OSError, urllib.error.URLError):
                    time.sleep(0.1)
            else:
                raise RuntimeError("Browser test server did not become ready")
            subprocess.run(
                ["node", "scripts/smoke_agent_browser.cjs"],
                cwd=root,
                env=environment,
                check=True,
                timeout=90,
            )
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    main()
