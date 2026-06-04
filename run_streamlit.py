"""Convenience entry point — run with: python run_streamlit.py

Launches the Streamlit web UI.
"""

import os
import subprocess
import sys


def run() -> None:
    """Start the Streamlit UI server."""
    app_path = os.path.join(os.path.dirname(__file__), "webdown", "presentation", "streamlit", "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path] + sys.argv[1:], check=False)


if __name__ == "__main__":
    run()
