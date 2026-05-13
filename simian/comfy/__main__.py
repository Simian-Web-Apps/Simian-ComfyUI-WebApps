"""Simian-Comfy command line interface."""

import argparse
import shutil
import os


parser = argparse.ArgumentParser(
    description="Simian ComfyUI cli.",
)
subparsers = parser.add_subparsers(dest="command", required=True, help="command that is executed")

# New app command
new_parser = subparsers.add_parser(
    "new",
    help="Start a new app by copying the Simian-ComfyUI template to a location to be specified.",
)
new_parser.add_argument(
    "folder",
    help="Full path to the folder to create a new Simian-ComfyUI app in from the template.",
)

# Start example command.
new_parser = subparsers.add_parser("start_example", help="Start the Simian-ComfyUI example app.")

# Help command
subparsers.add_parser("help")


def _new(folder: str):
    """Create a new app by copying the template to the specified folder."""
    if os.path.exists(folder) and len(os.listdir(folder)) > 0:
        print(os.listdir(folder))
        raise ValueError("Target folder for creating a Simian-ComfyUI app is not empty.")

    os.makedirs(folder, exist_ok=True)
    template_folder = os.path.join(os.path.dirname(__file__), "template")

    try:
        shutil.copytree(template_folder, folder, dirs_exist_ok=True)
        print("Simian-ComfyUI template copied to target folder.")
    except Exception as exc:
        print(f"Simian-Comfyui failed to copy the template across: {exc.message}")


# Parse the inputs given by the user, and execute the corresponding functionality.
args = parser.parse_args()

if args.command == "new":
    # New
    _new(args.folder)

elif args.command == "start_example":
    # Start example
    import simian.local

    simian.local.run("simian.comfy.examples.compositemasked.comfy_app")
else:
    # Help
    parser.print_help()
