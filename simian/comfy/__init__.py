"""Convert ComfyUI API workflow containing webapp API nodes to a Simian web app.

https://doc.simiansuite.com/simian-gui/index.html

All fields in the `app_data ` field of the `meta_data` dictionary are put in the corresponding
environment variables.

The ComfyUI server integration expects the following variables to be available in the environment.
- COMFY_SERVER: The ComfyUI server address to connect to. Defaults to 127.0.0.1:8188

- Adds a Basic authorization header with the following variables - if set.
  - COMFY_USER: The authorized user name to connect with the server.
  - COMFY_PASSWORD: The password for the user. Is encoded before it is put in the header.

Note that key-values in the `meta_data`["Application_data"] dictionary are added to the environment variables.


The `CONFIG` dictionary controls several aspects of the generated web app. overriding the options
before starting the app will affect how it looks and its behaviour.

- `app_title` (str, default: "Simian-ComfyUI app")
  Title shown in the navigation bar of the app.
- `app_subtitle` (str, default: "Demonstrator")
  Subtitle shown in the navigation bar of the app.
- `custom_results_download` (callable | None, default: None)
  Optional custom function that receives the `payload` and a list of file paths which it can show
  in custom components in the app, or upload the results to an external service.
- `default_results_download` (bool, default: True)
  When True, the app contains a ResultFile component that lets users download the images produced
  by the workflow.
- `panels_collapsible` (bool, default: True)
  Determines whether panels that contain grouped components are collapsible.
- `panels_collapsed` (bool, default: False)
  When `panels_collapsible` is True, this flag sets the initial collapsed state of the panels.
- `save_intermediates` (bool, default: False)
  If enabled, intermediate JSON representations of the interpreted workflow, the prompt sent to the
  server, and any generated mask images are written to the "generated" directory next to the
  workflow file. This is useful for debugging and troubleshooting.
"""

import base64
import glob
import io
import json
import math
import mimetypes
import os
import re
from typing import Sequence

import plotly.graph_objects as go
from PIL import Image, ImageDraw
from simian.gui import Form, component, component_properties, utils

import simian.comfy.connect
from simian.comfy.interpret_json import process_workflow_api

try:
    import webview

    webview.settings["ALLOW_DOWNLOADS"] = True
except ImportError:
    # Not run locally. In which case there is no problem.
    pass

CONFIG = {
    "app_title": "Simian-ComfyUI app",
    "app_subtitle": "Demonstrator",
    "custom_results_download": None,
    "default_results_download": True,
    "panels_collapsible": True,
    "panels_collapsed": False,
    "save_intermediates": False,
}

LOCATIONS = {
    "workflow": None,
    "simian_config": None,
}


# TODO: put Advanced components in own subpanels(?) or just hide until a central(?) tickbox is ticked.
# TODO: process tooltips
# TODO: show created images somewhere?
# TODO: Numeric inputs as sliders


def add_group(type_str: str, group_dict, parent) -> component.Component:
    """Add a layout component to the app.

    Args:
        type_str:   The type of the layout to add.
        group_dict: The inputs selected for the Grouping node.
        parent:     The location in the app to add the layout component to.

    Raises:
        ValueError: When the Grouping node has an unknown type selected.

    Returns:
        The created layout component to add other components to.
    """
    if type_str == "Section":
        # Always a new one
        new_comp = component.Panel(key=f"comp_{group_dict['id']}", parent=parent)
        new_comp.title = group_dict["_meta"]["title"]
        new_comp.collapsible = group_dict["inputs"]["collapsible"]
        if new_comp.collapsible:
            new_comp.collapsed = CONFIG["panels_collapsed"]

    elif type_str == "Tab":
        for comp in parent.components:
            if isinstance(comp, component.Tabs):
                tab_comp = comp
                break
        else:
            # No Tab component found in the for loop. Create a new one.
            tab_comp = component.Tabs(key=f"comp_{group_dict['id']}", parent=parent)

        new_comp = tab_comp.addTab(group_dict["_meta"]["title"], key=f"tab{group_dict['id']}")

    elif type_str == "Column":
        for comp in parent.components:
            if isinstance(comp, component.Columns):
                col_comp = comp
                new_width = math.floor(12 / (len(col_comp.columns) + 1))

                for col in col_comp.columns:
                    col.width = new_width
                break
        else:
            # No Columns component found in the for loop. Create a new one.
            col_comp = component.Columns(key=f"comp_{group_dict['id']}", parent=parent)
            new_width = 6

        new_comp = component_properties.Column(new_width)
        col_comp.addColumn(new_comp)

        descr = component.HtmlElement(f"label_{group_dict['id']}", parent=new_comp)
        descr.content = group_dict["_meta"]["title"]

    else:
        raise ValueError(f"Unknown Grouping type '{type_str}'.")

    return new_comp


def create_comp(node: dict) -> component.Component | None:
    """Create a Simian componenf from a ComfyUI webapp node.

    Args:
        node: ComfyUI webapp node definition.

    Returns:
        The Simian component that was created from the ComfyUI definition.
    """
    if node["class_type"] == "WebApp_Description":
        # Description.
        new_comp = component.HtmlElement(f"comp_{node['id']}")
        new_comp.content = node["inputs"]["description"]

    elif node["class_type"] in ["WebApp_Integerinput", "WebApp_Floatinput"]:
        # Numeric input
        new_comp = component.Number(f"comp_{node['id']}")
        new_comp.label = node["_meta"]["title"]
        new_comp.defaultValue = node["inputs"].get("default", None)
        component_properties.Validate.create(
            new_comp,
            min=node["inputs"].get("minimum", None),
            max=node["inputs"].get("maximum", None),
        )
        if node["class_type"] == "WebApp_Integerinput":
            new_comp.decimalLimit = 0

    elif node["class_type"] == "WebApp_BooleanInput":
        # Boolean input.
        new_comp = component.Checkbox(f"comp_{node['id']}")
        new_comp.label = node["_meta"]["title"]
        new_comp.defaultValue = node["inputs"].get("default", None)

    elif node["class_type"] == "WebApp_Stringinput":
        # Text input.
        if node["inputs"]["mode"] == "Multiline":
            new_class = component.TextArea
        else:
            new_class = component.TextField

        new_comp = new_class(f"comp_{node['id']}")
        new_comp.label = node["_meta"]["title"]
        new_comp.defaultValue = node["inputs"].get("default", None)

    elif node["class_type"] == "WebApp_Selectioninput":
        # Select component
        options = node["inputs"].get("options", [])
        full_options = node["inputs"].get("full_options", options)
        new_comp = component.Select(f"comp_{node['id']}")
        new_comp.label = node["_meta"]["title"]
        new_comp.setValues(
            labels=options, values=full_options, default=node["inputs"].get("default", None)
        )
        new_comp.multiple = node["inputs"].get("maximum", 1) > 1

    elif node["class_type"] == "WebApp_MaskedImageinput":
        # Masked image input.
        new_comp = component.Panel(f"cont_{node['id']}")
        new_comp.label = node["_meta"]["title"]
        new_comp.collapsible = CONFIG["panels_collapsible"]

        if new_comp.collapsible:
            new_comp.collapsed = CONFIG["panels_collapsed"]

        if node["inputs"]["is_image_used"]:
            upload_image = component.File(f"upload_{node['id']}", parent=new_comp)
            upload_image.filePattern = "image/*"

        plot_obj = component.Plotly(f"plot_{node['id']}", parent=new_comp)
        plot_obj.figure = go.Figure()
        plot_obj.figure.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, dragmode=False)
        plot_obj.aspectRatio = 2
        plot_obj.defaultValue["config"].update(
            {"modeBarButtonsToRemove": ["pan", "zoom", "zoomin", "zoomout"]}
        )
        plot_obj.customConditional = f"show = row.upload_{node['id']}.length > 0"
        plot_obj.redrawOn = "data"

        # Use the image selected in the File component as background in the Plotly component.
        plot_obj.calculateValue = (
            "var new_value = value ?? {layout: {}}; var comp = row.upload_"
            + node["id"]
            + "; if (comp.length > 0) { new_value.layout.images = [{'source': comp[0].url, "
            + "'x': 0.5, 'y': 0.5, 'xref': 'paper', 'yref': 'paper', 'xanchor': 'center', "
            + "'yanchor': 'middle', 'sizex': 1, 'sizey': 1, 'layer': 'below'}]; "
            + "new_value.layout.xaxis = {'range': [0, 1], 'visible': false}; "
            + "new_value.layout.yaxis = {'range': [0, 1], 'visible': false};} "
            + "else if (new_value?.layout === undefined) {} else {new_value.layout.images = []}; "
            + "value = new_value;"
        )

        if node["inputs"]["is_mask_used"]:
            # The image may be masked. Enable drawing shapes in the image.
            plot_obj.figure.update_layout(
                dragmode="drawrect",
                newshape_fillcolor="white",
                newshape_opacity=0.75,
            )

            plot_obj.defaultValue["config"].update(
                {
                    "modeBarButtonsToAdd": [
                        "drawclosedpath",
                        "drawcircle",
                        "drawrect",
                        "eraseshape",
                    ]
                }
            )

    else:
        # Not a normal component. Return a None.
        new_comp = None

    return new_comp


def scan_resources(calling_file: str):
    """Scan the surroundings of the given file for Comfy - Simian specific files.

    Args:
        calling_file: File to scan the surroundings of.
    """
    app_folder = os.path.dirname(calling_file)
    folder_jsons = glob.glob("*.json", root_dir=app_folder)

    for file in folder_jsons:
        full_file = os.path.join(app_folder, file)
        with open(full_file, "r") as f:
            try:
                json_dict = json.load(f)
            except Exception:
                continue

        if "inputs" in list(json_dict.values())[0]:
            LOCATIONS["workflow"] = full_file
            LOCATIONS["generated"] = os.path.join(os.path.dirname(full_file), "generated")
            os.makedirs(LOCATIONS["generated"], exist_ok=True)

        elif "rootlevel" in json_dict:
            LOCATIONS["simian_config"] = full_file


def convert_api_to_app(form: Form) -> None:
    """Convert ComfyUI workflow API with webapp nodes to a Simian web app.

    Args:
        form: Simian Form to add the components to.
    """
    if LOCATIONS["workflow"] is not None:
        app_nodes_dict = process_workflow_api(LOCATIONS["workflow"])

        if CONFIG.get("save_intermediates", False):
            with open(os.path.join(LOCATIONS["generated"], "interpreted.json"), "w+") as f:
                json.dump(app_nodes_dict, f)

        root_cont = app_nodes_dict.pop("root", [])

        has_run_button = any([node["class_type"] == "WebApp_Button" for node in root_cont])

        for node_dict in root_cont:
            node_dict_to_component(app_nodes_dict, node_dict, 0, form)

        # When no RunWorkflow button added in the definition, add one here.
        if not has_run_button:
            button = component.Button("run_workflow", form)
            button.label = "Run workflow"
            button.setEvent("RunWorkflow")

        if CONFIG["default_results_download"]:
            results_panel = component.Panel("results_panel", form)
            results_panel.label = "Results"
            results_panel.collapsible = True
            results_panel.collapsed = True

            results_file = component.ResultFile("results_file", results_panel)
            results_file.label = "Files created in workflow"

    else:
        descr = component.HtmlElement("NoResourcesDetected", form)
        descr.content = "No workflow API detected."


def node_dict_to_component(all_nodes: dict, node: dict, level: int, parent) -> None:
    """Node dict to component conversion function."""
    if (new_node := create_comp(node)) is not None:
        # A compent was created in create_comp. Just add it to the parent.
        parent.addComponent(new_node)

    elif node["class_type"] == "WebApp_Grouping":
        group_type = node["inputs"]["mode"]

        # TODO: what if parent is a Panel and we are adding a DataGrid with comps. Remove the panel, as not needed for grouping

        child_nodes = all_nodes[node["id"]]

        if group_type != "Repeating":
            # Standard grouping node. Just create the layout component.
            new_sub_comp = add_group(type_str=group_type, group_dict=node, parent=parent)

        else:
            # Repeating component - create a DataGrid as parent with a configurable number of rows.
            new_sub_comp = parent
            assert not isinstance(new_sub_comp, component.DataGrid), (
                "Nesting Repeated Groupings is not supported yet."
            )

            new_sub_comp = component.DataGrid(key=f"rep_{node['id']}", parent=new_sub_comp)
            component_properties.Validate.create(
                new_sub_comp,
                minLength=node["inputs"].get("mode.minimum", 1),
                maxLength=node["inputs"].get("mode.maximum", 2),
            )

        for child in child_nodes:
            node_dict_to_component(all_nodes, child, level=level + 1, parent=new_sub_comp)

    else:
        print(node)


def gui_init(meta_data: dict) -> dict:
    """Initializes the form.

    Initialization of the form and the components therein.

    Returns:
        payload:    Form definition, as {"form": Form object}
    """
    _init_env(meta_data)
    form = Form()

    convert_api_to_app(form)

    if LOCATIONS["workflow"] is not None and CONFIG.get("save_intermediates", False):
        with open(os.path.join(LOCATIONS["generated"], "created_form.json"), "w+") as f:
            print(form.jsonEncode(), file=f)

    return {
        "form": form,
        "navbar": {
            "title": CONFIG["app_title"],
            "subtitle": CONFIG["app_subtitle"],
        },
    }


def gui_event(meta_data: dict, payload: dict) -> dict:
    """Event handling of the application.

    Args:
        meta_data:      Form meta data.
        payload:        Current status of the Form's contents.

    Returns:
        payload:        Updated Form contents.
    """
    _init_env(meta_data)
    Form.eventHandler(
        RunWorkflow=run_workflow,
    )
    callback = utils.getEventFunction(meta_data, payload)
    return callback(meta_data, payload)


def _init_env(meta_data: dict):
    """Set the environment variables and module variables."""
    for key, value in meta_data["application_data"].items():
        os.environ[key] = value

    simian.comfy.connect.init()


def run_workflow(meta_data, payload) -> dict:
    """Run workflow event process."""
    with open(LOCATIONS["workflow"]) as f:
        prompt = json.load(f)

    process_component_values(prompt, payload["submission"]["data"])

    if CONFIG.get("save_intermediates", False):
        # Save the prompt we are about to send to a local file for troubleshooting.
        with open(os.path.join(LOCATIONS["generated"], "sent_prompt.json"), "w+") as f:
            json.dump(prompt, f)

    _prompt_id, files = simian.comfy.connect.run_workflow(
        prompt,
        session_id=meta_data["session_id"],
    )

    session_folder = utils.getSessionFolder(meta_data, create=True)

    file_names = []
    for node_id in files:
        for image_data in files[node_id]:
            byte_stream = io.BytesIO(image_data["data"])

            # Save the result image in the session folder of the app.
            image = Image.open(byte_stream)
            filename = os.path.join(session_folder, image_data["meta"]["filename"])
            image.save(filename)
            image.close()

            file_names.append(filename)

    if len(file_names) > 0:
        if CONFIG["default_results_download"]:
            mime_types = [mimetypes.guess_type(file)[0] for file in file_names]
            component.ResultFile.upload(
                file_names,
                mime_types,
                meta_data,
                payload,
                key="results_file",
                append=True,
            )

        if CONFIG["custom_results_download"] is not None:
            try:
                CONFIG["custom_results_download"](payload, file_names)
            except Exception as exc:
                utils.addAlert(payload, f"Custom results processing failed: {exc}", "danger")

        utils.addAlert(payload, "Results files detected and obtained from server.", "info")
    else:
        utils.addAlert(payload, "No results files detected.", "info")

    return payload


def process_component_values(prompt: dict, data: dict):
    """Process the values selected in the app and put them in the prompt.

    Args:
        prompt: dictionary with the workflow API that we need to fill with the app values.
        data: dictionary with app values to insert into the prompt.
    """
    app_nodes_dict = process_workflow_api(LOCATIONS["workflow"])

    # Insert the values from the app.
    for comp_id, value in data.items():
        match_id = re.search(r"\d+$", comp_id)

        if match_id is None:
            # The workflow API does not contain an item with the same identifier as the component.
            # Nothing to put the value in. Skip
            continue
        workflow_id = match_id.group()

        if isinstance(value, str) or not isinstance(value, Sequence):
            # Value must always be in a list. This eases further processing.
            value = [value]

        if workflow_id in app_nodes_dict:
            # Group with sub-components,

            # Process the values in the rows at the same time; they need to be put in the same part of the prompt.
            process_component_values(prompt, {k: [dic[k] for dic in value] for k in value[0]})

        elif prompt[workflow_id]["class_type"] == "WebApp_MaskedImageinput":
            # Dealing with an image
            if comp_id.startswith("upload") and len(value) > 0:
                # Get the base64 encoded representation of the image.
                prompt[workflow_id]["inputs"]["image_base64"] = json.dumps(
                    [process_image_to_str(item) for item in value]
                )
            elif comp_id.startswith("plot") and len(value) > 0:
                # Get the base64 encoded representation of the mask.
                prompt[workflow_id]["inputs"]["mask_base64"] = json.dumps(
                    [process_mask_to_str(item) for item in value]
                )
            else:
                # Component does not contain a value to put in the prompt.
                pass
        else:
            prompt[workflow_id]["inputs"]["value_from_interface"] = json.dumps(value)


def process_image_to_str(file_data: list[dict] | list[dict]) -> str:
    """Process the image file selected in the File component.

    Args:
        file_data: Meta data of the selected file.

    Returns:
        Base64 encoded string of the selected image file.
    """
    if isinstance(file_data, list) and len(file_data) > 0:
        file_data = file_data[0]
    elif isinstance(file_data, dict):
        pass
    elif isinstance(file_data, str) and os.path.isfile(file_data):
        file_data = {"url": utils.encodeImage(file_data)}
    else:
        file_data = {}

    url = file_data.get("url", "")

    return re.sub(r"^data:image/\w+;base64,", "", url)


def process_mask_to_str(plot_data: dict) -> str:
    """Process the image mask that was drawn in the Plotly component.

    Args:
        plot_data: Contents of the masked image.

    Returns:
        Base64 encoded string of the image mask.
    """
    plot_obj = utils.Plotly(payload_value=plot_data)
    backgrounds = plot_obj.layout.get("images", [])
    shapes = plot_obj.getShapes()

    if len(backgrounds) == 0 or len(shapes) == 0:
        # No background image or no shapes drawn.
        return ""

    else:
        source_str = re.sub(r"^data:image/\w+;base64,", "", backgrounds[0].get("source", ""))
        decoded_bytes = base64.b64decode(source_str)
        byte_stream = io.BytesIO(decoded_bytes)
        im = Image.open(byte_stream)

        new_image = Image.new("1", im.size, 0)
        fill_val = 1
        mask_image = ImageDraw.Draw(new_image)

        # Both axes have a range of [0, 1], with a plot aspect ratio of 2. Below the coordinates
        # are converted to pixels so that we can draw the mask shapes and convert it to a string.
        unit_size_x = max([im.size[0], 2 * im.size[1]])
        unit_size_y = max([im.size[0] / 2, im.size[1]])
        offset = [(unit_size_x - im.size[0]) / 2, (unit_size_y - im.size[1]) / 2]

        for shape in shapes:
            coords = list(
                zip(
                    sorted([x * unit_size_x - offset[0] for x in shape["x"]]),
                    sorted([im.size[1] - y * unit_size_y + offset[1] for y in shape["y"]]),
                )
            )
            if shape["type"] == "rect":
                mask_image.rectangle(coords, fill_val, 1)
            elif shape["type"] == "circle":
                mask_image.ellipse(coords, fill_val, 1)
            elif shape["type"] == "path":
                mask_image.polygon(coords, fill_val, 1)

    buffered = io.BytesIO()
    new_image.save(buffered, format="jpeg")

    if CONFIG.get("save_intermediates", False):
        new_image.save(os.path.join(LOCATIONS["generated"], "mask.png"))

    return base64.b64encode(buffered.getvalue()).decode("utf-8")
