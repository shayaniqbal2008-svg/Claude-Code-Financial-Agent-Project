import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
import uvicorn

BASE_DIR = Path(__file__).parent.parent
DASHBOARD_URL = "http://localhost:3000"
PORT = 3000


def create_icon_image() -> Image.Image:
    img = Image.new("RGB", (64, 64), color="#0d1117")
    draw = ImageDraw.Draw(img)
    # Simple "FA" logo in accent blue
    draw.rectangle([4, 4, 60, 60], outline="#58a6ff", width=2)
    draw.text((14, 18), "FA", fill="#58a6ff")
    return img


def open_dashboard():
    webbrowser.open(DASHBOARD_URL)


def run_agent_now():
    agent_script = BASE_DIR / "agent" / "main.py"
    subprocess.Popen([sys.executable, str(agent_script)], cwd=str(BASE_DIR))


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
        pystray.MenuItem("Open Dashboard", lambda: open_dashboard()),
        pystray.MenuItem("Run Agent Now", lambda: run_agent_now()),
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
