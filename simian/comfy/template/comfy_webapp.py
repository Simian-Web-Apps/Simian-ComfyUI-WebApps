"""Simian ComfyUI web app."""

# Import necessary Simian-Comfy resources.
from simian.comfy import gui_init, gui_event, CONFIG, scan_resources

CONFIG["default_results_download"] = True

# Look for files in the local folder.
scan_resources(__file__)

# The app_data contents are converted to environment variables.
app_data = {
    # "COMFY_SERVER": "127.0.0.1:8188",
    # "COMFY_USER": "user_name",
    # "COMFY_PASSWORD": "password",
}

if __name__ == "__main__":
    from simian.local import run

    run("comfy_webapp", app_data=app_data)
