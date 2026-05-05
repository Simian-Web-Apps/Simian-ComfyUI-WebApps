# Simian-ComfyUI-WebApps

The [Simian WebApps](https://simiansuite.com/) - [ComfyUI](https://docs.comfy.org/) integration library implements the [ComfyUI WebApp API definition](github.com/MonkeyProof-Solutions-BV/ComfyUI_webapp) for Simian Apps*.

\* Note that the Simian Portal is licensed.

## Getting started

- Install this package in your Python environment. Simian-GUI and Simian-local will be installed as well.
- Install the ComfyUI WebApp API custom nodes in your ComfyUI server.
- From the command line run `python -m simian.comfy start_example` to start the example app.
  - If the ComfyUI server is running on localhost, the app can run its workflow on the server.

## Creating a new app

- From the command line run `python -m simian.comfy new target_folder` to copy the template contents provided with this library into the specified folder.
- Add ComfyUI WebApp API nodes to your workflow, and add extra information you want to show in the app.
- Export the workflow API and put the created file in the new app folder.
- Optional: modify the app configuration
- When not running ComfyUI on localhost, configure the app to connect with the ComfyUI server.
- Start the app locally using the Simian-local run method.

## Features

- Auto-dectects the ComfyUI workflow API file when put next to a copy of the library's template.
