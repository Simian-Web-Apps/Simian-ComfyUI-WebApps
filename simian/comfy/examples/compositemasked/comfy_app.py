"""Simian ComfyUI example web app."""

# Import necessary Simian-Comfy resources.
from simian.comfy import gui_init, gui_event, CONFIG, scan_resources

# Look for files in the local folder.
scan_resources(__file__)
