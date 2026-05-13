# Simian-ComfyUI-WebApps

The [Simian WebApps](https://simiansuite.com/) - [ComfyUI](https://docs.comfy.org/) integration package implements the [ComfyUI WebApp API definition](github.com/MonkeyProof-Solutions-BV/ComfyUI_webapp) for Simian Apps*.

The ComfyUI WebApp API nodes allow you to define web app interfaces directly within ComfyUI workflows. This package interprets those definitions to automatically generate a Simian app, eliminating the need for additional coding.

\* Note that the Simian Portal is licensed.

## Getting started

- Install this package in your Python environment. Simian-GUI and Simian-local will be installed as well.
- Install the ComfyUI WebApp API custom nodes in your ComfyUI server.
- From the command line run `python -m simian.comfy start_example` to start the example app.
  - If the ComfyUI server is running on localhost, the app can run its workflow on the server.

Note that the example app consists of:

- a css folder with a small `style.css` file to improve the appearance of the app.
- comfy_app.py: The Simian app module with 4 lines of code that imports the functionality of this package and applies it on the next file:
- DemoImageInputNodesAPI.json: The exported ComfyUI workflow API with WebApp API nodes that define the inputs and connect them with the image composite nodes.

## Creating a new app

- From the command line run `python -m simian.comfy new target_folder` to create a new app folder with the template contents provided with this library.
- Design your workflow in ComfyUI and add WebApp API nodes for UI elements and additional information you want to include in your app.
- Export the workflow API from ComfyUI and place the resulting file in your new app folder.
- Optional:
  - Customize the app CONFIG as needed
  - Configure the app to connect to a remote ComfyUI server if it's not running on localhost
- Launch the app locally using the Simian-local run method.

## Features

- Auto-dectects the ComfyUI workflow API file when put next to a copy of the library's template, and creates a webapp based on the WebApp API nodes in the workflow.
- Command line interface to create new apps from a template, and a start_example option that runs the example provided in the package.
- `Application data` fields from the Simian Portal are set as environment variables in the Python session.

## Extending the app

The standard Simian-Comfy functionality creates a functional app from your workflow API. It is possible to extend the standard application with extra Simian-gui controls and event callbacks, which are described in more detail in the [documentation](https://doc.simiansuite.com/simian-gui/index.html)

### Adding controls to the app

In the app module create a custom `gui_init` function. In it:

- run the aliased `simian.comfy` `gui_init` function to convert the workflow API to a form.
- Add the extra components to the form.

```python
from simian.gui import component
from simian.comfy import gui_init as gui_init_standard

def gui_init(meta_data):
    # Run the standard gui_init function to convert the worklow API into a form.
    form_dict = gui_init_standard(meta_data)

    # Add a Button to the root of the form, and set it to fire a custom event.
    button = component.Button("extra_button", form_dict["form"])
    button.label = "Click me"
    button.setEvent("CustomEvent")

    return form_dict
```

### Handling extra events

In the app module:

- create a custom `gui_event` function. In it:
  - register extra event handler functions.
  - run the aliased `simian.comfy` `gui_event` function to perform the events coming from the frontend.

- Add a simian-gui event function that performs the necessary operations on the payload.

```python
from simian.gui import Form
from simian.comfy import gui_event as gui_event_standard

def gui_event(meta_data: dict, payload: dict) -> dict:
    # Register a callback function for the "CustomEvent" event.
    Form.eventHandler(
        CustomEvent=custom_event,
    )

    # Run the standard gui_event function which will run all registered event handlers.
    gui_event_standard(meta_data, payload)

    return payload

def custom_event(meta_data: dict, payload: dict) -> dict:
    """Process the extra event."""
    print("Custom event callback function executed")
    return payload
```

### Custom results handling

The default results handling mechanism in Simian-ComfyUI apps makes the created images available for download via a `ResultFile` component. You can turn this off by setting the `default_results_download` configuration option to False:

```python
CONFIG["default_results_download"] = False
```

To implement your own mechanism you should:

- add extra Simian components to your app in the `gui_init` function (as shown earlier) to show the results.
- write a function that accepts the payload dict and a list of backend-side file paths. The function must update the payload values of the components you have added to show the results in the app.
- register the function in the `custom_results_download` option of the configuration to make sure it is called when new files are available.

```python
def show_results(payload: dict, files: list[str]) -> None:
    """Show the results in the app."""
    ...

# Register the custom results function to ensure it is used when new results are detected.
CONFIG["custom_results_download"] = show_results
```

When you keep the default results download option, and specify and register a custom function, the results will be downloadable from the `ResultFile` and be processed by your own function.
