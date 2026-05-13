"""ComfyUI server - websocket connection.

Looks for environment variables
- COMFY_SERVER: The ComfyUI server address to connect to. Defaults to 127.0.0.1:8188

- Adds a Basic authorization header with the following variables - if set.
  - COMFY_USER: The authorized user name to connect with the server.
  - COMFY_PASSWORD: The password for the user. Is encoded before it is put in the header.
"""

import base64
import json
import os
import urllib
import urllib.request
import uuid

import websocket

SS = {
    "WS": "ws",
    "HTTP": "http",
}


def init():
    """Setup the environment"""
    SS["SERVER_ADDRESS"] = os.getenv("COMFY_SERVER", "127.0.0.1:8188")
    SS["AUTH"] = os.getenv("COMFY_USER")

    if SS["AUTH"]:
        # Authenticated connection. Use the secure protocol.
        SS["WS"] += "s"
        SS["HTTP"] += "s"


def run_workflow(
    workflow: dict, session_id: str, expected_files: list[str] = list()
) -> tuple[str | None, dict]:
    """Start the workflow and return the first image.

    Args:
        workflow:       ComfyUI workflow definition.
        session_id:     App session identifier.
        expected_files: List of non-image files that are expected to be created.

    Returns:
        prompt_id:      Identifier of the workflow prompt.
        files:          Dict with the generated images.
    """
    if SS["AUTH"]:
        pw = base64.b64encode(
            f"{os.getenv('COMFY_USER')}:{os.getenv('COMFY_PASSWORD')}".encode()
        ).decode()
        opts = {"header": {"Authorization": "Basic %s" % pw}}
    else:
        opts = {}

    # files = get_images(ws, workflow, session_id)
    prompt_id = str(uuid.uuid4())

    ws = websocket.WebSocket()
    ws.connect("{}://{}/ws?clientId={}".format(SS["WS"], SS["SERVER_ADDRESS"], session_id), **opts)

    queue_prompt(workflow, session_id, prompt_id)

    files = {}
    current_node = ""
    while True:
        out = ws.recv()

        if isinstance(out, str):
            message = json.loads(out)
            data = message.get("data", {})

            if message["type"] == "executing":
                if data["prompt_id"] == prompt_id:
                    if data["node"] is None:
                        break  # Execution is done
                    else:
                        current_node = data["node"]

        else:
            if workflow[current_node]["class_type"] == "SaveImageWebsocket":
                images_output = files.get(current_node, [])
                images_output.append(
                    {
                        "meta": {"filename": str(uuid.uuid4()) + ".png", "type": current_node},
                        "data": out[8:],
                    }
                )
                files[current_node] = images_output

    files = process_history(prompt_id)

    for file in expected_files:
        # Append list with files expected to be returned from the workflow.
        bb = get_image(file, "", "output")
        files |= {file: bb}
    ws.close()

    return None, files


def _build_request(url_path: str, **req_values):
    request = urllib.request.Request(
        "{}://{}/{}".format(SS["HTTP"], SS["SERVER_ADDRESS"], url_path), **req_values
    )

    if SS["AUTH"]:
        pw = base64.b64encode(
            f"{os.getenv('COMFY_USER')}:{os.getenv('COMFY_PASSWORD')}".encode()
        ).decode()
        request.add_header("Authorization", "Basic %s" % pw)

    with urllib.request.urlopen(request) as response:
        return response.read()


def queue_prompt(prompt, session_id, prompt_id):
    p = {"prompt": prompt, "client_id": session_id, "prompt_id": prompt_id}
    data = json.dumps(p).encode("utf-8")

    _build_request("api/prompt", data=data)


def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)

    return _build_request(f"view?{url_values}")


def get_history(prompt_id):
    return json.loads(_build_request(f"api/history/{prompt_id}"))


def get_images(node_id: str, node_output: dict, output_images: dict) -> None:
    images_output = []
    if "images" in node_output:
        for image in node_output["images"]:
            image_data = get_image(image["filename"], image["subfolder"], image["type"])
            images_output.append({"meta": image, "data": image_data})
    output_images[node_id] = images_output


def process_history(prompt_id: str, start_idx: int = 0) -> dict[str, list]:
    history = get_history(prompt_id).get(prompt_id, {})

    output_images = {}

    for node_id in history.get("outputs", []):
        node_output = history["outputs"][node_id]
        get_images(node_id=node_id, node_output=node_output, output_images=output_images)

    return output_images
