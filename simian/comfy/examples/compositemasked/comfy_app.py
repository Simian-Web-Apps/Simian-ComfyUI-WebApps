"""Simian ComfyUI example web app.

Can be run from the command line as: python -m simian.comfy start_example.
Requires a ComfyUI server to be running locally on "127.0.0.1:8188".
"""

# Import necessary Simian-Comfy resources.
from simian.comfy import gui_init, gui_event, CONFIG, scan_resources

CONFIG["save_intermediates"] = True

# Look for files in the local folder.
scan_resources(__file__)
