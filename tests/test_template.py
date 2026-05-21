"""Tests for the example and template."""

import base64
import os.path
from simian.gui import testing, utils
from simian.comfy import CONFIG
import plotly
from unittest import mock

YCOORD_ID = "34"
BACKGROUND_ID = "30"
IMAGE_ID = "31"
EXAMPLE_FILE = os.path.join(os.path.dirname(__file__), "example.png")


class TestTemplate(testing.Testing):
    namespace = "simian.comfy.template.comfy_webapp"
    add_meta_data = {"application_data": {}}

    def test_startup(self):
        # The template does not contain a ComfyUI workflow, so the form will only contain a label that mentions this.
        assert len(self.form_obj.components) == 1


def _mock_connect_run(*args, **kwargs):
    """Mock function for the ComfyUI connection.

    Prevent trying to set up a websocket connection with a non-existing server.
    """
    with open(EXAMPLE_FILE, "rb") as file:
        base64_data = base64.b64decode(base64.b64encode(file.read()))

    image_data = {"IMAGE_ID": [{"meta": {"filename": "example.png"}, "data": base64_data}]}

    return {}, image_data


def _mock_custom_results_function(cache: dict):
    def inner(payload: dict, file_list: list[str]):
        cache["count"] = len(file_list)

    return inner


class TestExample(testing.Testing):
    namespace = "simian.comfy.examples.compositemasked.comfy_app"
    add_meta_data = {"application_data": {}}

    def test_startup(self):
        # Change the Y-coordinate value.
        self.type(f"comp_{YCOORD_ID}", value=27)
        gui_value, _ = self.getSubmissionData(f"comp_{YCOORD_ID}")
        assert 27 == gui_value

    @mock.patch("simian.comfy.connect.run_workflow", _mock_connect_run)
    def test_run_workflow(self):
        cache = {}
        CONFIG["custom_results_download"] = _mock_custom_results_function(cache)
        CONFIG["save_intermediates"] = True

        # Put the example figure in the background and object figure file components.
        self.choose(f"upload_{BACKGROUND_ID}", EXAMPLE_FILE)
        self.choose(f"upload_{IMAGE_ID}", EXAMPLE_FILE)
        self.type(f"comp_{YCOORD_ID}", value=400)

        # Put the object image in Plotly component and draw some shapes.
        plot_obj = utils.Plotly()
        plot_obj.figure = plotly.graph_objects.Figure()
        plot_obj.figure.update_layout(images=[{"source": utils.encodeImage(EXAMPLE_FILE)}])

        for shape in ["rect", "circle", "path"]:
            plot_obj.addShape({"type": shape, "x": [0.2, 0.4], "y": [0.3, 0.5]})

        self.payload["submission"]["data"][f"plot_{IMAGE_ID}"] = plot_obj.preparePayloadValue()

        # Press the Run Workflow button.
        self.press("run_workflow")

        # Verify that the custom results function received the mocked results figure.
        assert cache["count"] == 1
