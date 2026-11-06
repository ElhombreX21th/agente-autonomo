"""End-to-end browser test with synthetic login, form, logout and human pause."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import tempfile
import threading
from urllib.parse import parse_qs

from agent_v3.browser_batch import run_batch
from agent_v3.browser_workflow import BrowserApproval, BrowserStep, BrowserWorkflow


LOGIN = b"""<!doctype html><html><body><form method='post' action='/login'>
<label>Email <input id='email' name='email'></label>
<label>Password <input id='password' name='password' type='password'></label>
<button id='login'>Log in</button></form></body></html>"""
PROFILE = b"""<!doctype html><html><body><main id='profile'>
<form method='post' action='/profile'>
<label>Headline <input id='headline' name='headline'></label>
<label>Sector <select id='sector' name='sector'><option value='operations'>Operations</option></select></label>
<label><input id='newsletter' name='newsletter' type='checkbox'> Newsletter</label>
<button id='save'>Save</button></form>
<form method='post' action='/logout'><button id='logout'>Log out</button></form>
</main></body></html>"""


class Handler(BaseHTTPRequestHandler):
    saved = None

    def log_message(self, format, *args):
        pass

    def send_html(self, body, status=200, cookie=None):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        if cookie:
            self.send_header("Set-Cookie", cookie)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/login":
            self.send_html(LOGIN)
        elif self.path == "/challenge":
            self.send_html(b"<main id='captcha'>Human verification required</main>")
        else:
            self.send_html(b"not found", 404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        form = parse_qs(self.rfile.read(length).decode())
        if self.path == "/login":
            if form == {
                "email": ["master@example.test"],
                "password": ["synthetic-secret"],
            }:
                self.send_html(
                    PROFILE, cookie="session=synthetic; HttpOnly; SameSite=Strict"
                )
            else:
                self.send_html(b"unauthorized", 401)
        elif self.path == "/profile":
            Handler.saved = form
            self.send_html(
                b"<main id='saved'>Saved synthetic profile"
                b"<form method='post' action='/logout'>"
                b"<button id='logout'>Log out</button></form></main>"
            )
        elif self.path == "/logout":
            self.send_html(
                LOGIN, cookie="session=; Max-Age=0; HttpOnly; SameSite=Strict"
            )
        else:
            self.send_html(b"not found", 404)


def workflow(port):
    return BrowserWorkflow(
        name="Synthetic login, profile form and logout",
        allowed_hosts=["127.0.0.1"],
        steps=[
            BrowserStep(action="goto", value=f"http://127.0.0.1:{port}/login"),
            BrowserStep(
                action="fill", selector="#email", secret_env="TEST_LOGIN_EMAIL"
            ),
            BrowserStep(
                action="fill", selector="#password", secret_env="TEST_LOGIN_PASSWORD"
            ),
            BrowserStep(action="click", selector="#login"),
            BrowserStep(action="wait_for", selector="#profile"),
            BrowserStep(
                action="fill", selector="#headline", value="Synthetic improved headline"
            ),
            BrowserStep(action="select", selector="#sector", value="operations"),
            BrowserStep(action="check", selector="#newsletter"),
            BrowserStep(action="click", selector="#save"),
            BrowserStep(action="wait_for", selector="#saved"),
            BrowserStep(action="screenshot", value="completed.png"),
            BrowserStep(action="logout", selector="#logout"),
            BrowserStep(action="wait_for", selector="#login"),
        ],
    )


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        task = workflow(server.server_port)
        challenge = BrowserWorkflow(
            name="Synthetic human challenge",
            allowed_hosts=["127.0.0.1"],
            steps=[
                BrowserStep(
                    action="goto",
                    value=f"http://127.0.0.1:{server.server_port}/challenge",
                ),
                BrowserStep(
                    action="human_challenge",
                    value="A person must complete this challenge; bypass is forbidden.",
                ),
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            results = run_batch(
                [task],
                {task.digest(): BrowserApproval(task.digest(), role="master")},
                Path(directory) / "login-form",
                environment={
                    "TEST_LOGIN_EMAIL": "master@example.test",
                    "TEST_LOGIN_PASSWORD": "synthetic-secret",
                },
            )
            assert results[0].status == "completed", results
            assert Handler.saved == {
                "headline": ["Synthetic improved headline"],
                "sector": ["operations"],
                "newsletter": ["on"],
            }
            challenged = run_batch(
                [challenge, task],
                {},
                Path(directory) / "challenge",
            )
            assert len(challenged) == 1
            assert challenged[0].status == "human_action_required"
        print(
            "Browser autonomy: login, secret fields, form, select, checkbox, save and human-challenge pause OK"
        )
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
