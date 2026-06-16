import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
import uvicorn

BASE_DIR = Path(__file__).parent.parent
PORT = 3000
DASHBOARD_URL = f"http://localhost:{PORT}"


def create_icon_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), color="#0d1117")
    draw = ImageDraw.Draw(img)
    # Simple "FA" logo in accent blue
    draw.rectangle([4, 4, 60, 60], outline="#58a6ff", width=2)
    draw.text((14, 18), "FA", fill="#58a6ff")
    return img


def open_dashboard():
    webbrowser.open(DASHBOARD_URL)


_agent_proc: subprocess.Popen | None = None


def run_agent_now():
    global _agent_proc
    if _agent_proc is not None and _agent_proc.poll() is None:
        return  # already running
    agent_script = BASE_DIR / "agent" / "main.py"
    if not agent_script.exists():
        return
    _agent_proc = subprocess.Popen([sys.executable, str(agent_script)], cwd=str(BASE_DIR))


def start_server():
    uvicorn.run(
        "dashboard.server:app",
        host="127.0.0.1",
        port=PORT,
        log_level="error",
    )


def main():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    menu = pystray.Menu(
        pystray.MenuItem("Open Dashboard", open_dashboard),
        pystray.MenuItem("Run Agent Now", run_agent_now),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", lambda icon, item: icon.stop()),
    )

    icon = pystray.Icon(
        name="FinancialAgent",
        icon=create_icon_image(),
        title="Financial Agent",
        menu=menu,
    )
    icon.run()


if __name__ == "__main__":
    main()
