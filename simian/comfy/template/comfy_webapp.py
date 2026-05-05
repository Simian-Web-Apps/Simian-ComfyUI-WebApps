"""Simian ComfyUI web app."""

from simian.local import run

# Import necessary Simian-Comfy resources.
from simian.comfy import gui_init, gui_event, CONFIG, scan_resources

# Look for files in the local folder.
scan_resources(__file__)

# Modify the configuration.
CONFIG["group_nesting"] = ["tabs"]

if __name__ == "__main__":
    run("comfy_webapp", debug=True, show_refresh=True)
