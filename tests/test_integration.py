"""Tests for the integration of the example app and a ComfyUI server.

The tests are skipped when no connection with a ComfyUI server can be made on localhost.
"""

import os.path
import urllib.error
import urllib.request

import plotly
import pytest
from simian.gui import testing, utils

from simian.comfy import CONFIG

YCOORD_ID = "34"
BACKGROUND_ID = "30"
IMAGE_ID = "31"
EXAMPLE_FILE = os.path.join(os.path.dirname(__file__), "example.png")


def try_connection():
    conn = False
    request = urllib.request.Request("http://127.0.0.1:8188/")
    try:
        with urllib.request.urlopen(request) as response:
            conn = response.status == 200
    except urllib.error.URLError:
        pass
    return conn


@pytest.mark.skipif(
    condition=try_connection() is False, reason="A ComfyUI server must be available for this test."
)
class TestExample(testing.Testing):
    namespace = "simian.comfy.examples.compositemasked.comfy_app"
    add_meta_data = {"application_data": {}}

    def test_run_example_workflow(self):
        """Test the integration between the Simian-Comfy example app and the ComfyUI server."""
        CONFIG["save_intermediates"] = False

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

        results, _ = self.getSubmissionData("results_file")
        assert len(results) == 1


if __name__ == "__main__":
    pytest.main()  # ["-k", "not test_cli"])  # ["-k", "TestTemplate"])
