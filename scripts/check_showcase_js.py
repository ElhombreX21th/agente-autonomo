"""Check the real embedded showcase script with Node.js (no packages needed)."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
html = (root / "upwork_showcase_2026/web/showcase.html").read_text()
script = html.split("<script>", 1)[1].split("</script>", 1)[0]
with tempfile.TemporaryDirectory() as directory:
    source = Path(directory) / "showcase.js"
    source.write_text(script)
    subprocess.run(["node", "--check", str(source)], check=True)
print("Showcase JavaScript syntax: OK")
