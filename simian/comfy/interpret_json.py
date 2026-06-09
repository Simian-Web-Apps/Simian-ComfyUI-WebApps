"""Utility module to extract WebApp API information from workflow API jsons."""

import json
import re


def process_workflow_api(input_file: str) -> dict[str, list]:
    """Process Workflow API .json file.

    Reorder the workflow into a dict with per parent the sorted list of children. Nodes without a
    parent are put in under the 'root' key.
    The 'order' inputs are evaluated and are converted to integers where needed.
    The node id is put in the node dict.

    Args:
        input_file:         Workflow API export .json file to process.

    Returns:
        Dictionary with for each parent node the children nodes.
    """
    with open(input_file) as f:
        workflow_dict = json.load(f)
        f.seek(0, 0)
        workflow_str = f.read()

    # Check API json: all root children are node dicts. No 'nodes' and 'links' lists.
    assert "nodes" not in workflow_dict and "links" not in workflow_dict

    app_nodes = {"root": []}

    for node_id, node_dict in workflow_dict.items():
        if node_dict["class_type"].startswith("WebApp_"):
            # Node is a webapp definition node.
            node_dict["id"] = node_id

            if node_dict["inputs"].get("parent", "") == "":
                # Node is not linked to a Parent, so add to root.
                app_nodes["root"].append(node_dict)
            elif (parent_id := node_dict["inputs"]["parent"][0]) in app_nodes:
                app_nodes[parent_id].append(node_dict)
            else:
                app_nodes[parent_id] = [node_dict]

            if node_dict["class_type"] == "WebApp_MaskedImageinput":
                # Special case - MaskedImage node. Mask and Image could be unused in the workflow.
                # The UI should reflect this.
                node_dict["inputs"]["is_image_used"] = (
                    re.search(rf'\[\s*"{node_id}",\s*0\s*\]', workflow_str) is not None
                )
                node_dict["inputs"]["is_mask_used"] = (
                    re.search(rf'\[\s*"{node_id}",\s*1\s*\]', workflow_str) is not None
                )

            node_dict["inputs"]["order"] = get_order(workflow_dict, node_dict)

    # All nodes have been put in their respective lists of nodes. Now sort them by the order.
    for list_id, nodes_list in app_nodes.items():
        nodes_order_nrs = [node["inputs"]["order"] for node in nodes_list]
        nodes_titles = [node["_meta"]["title"] for node in nodes_list]
        node_ids = [node["id"] for node in nodes_list]
        sorted_ids = [id for _, _, id in sorted(zip(nodes_order_nrs, nodes_titles, node_ids))]

        app_nodes[list_id] = [nodes_list[node_ids.index(id)] for id in sorted_ids]

    return app_nodes


def get_order(workflow_dict: dict, node: dict) -> int:
    """Determine the 'order' number of the node.
    - Integer defined in the widget itself.
    - Link to another webapp node: get its order and increase by 1.
    - Link to any other integer output slot; set to default."""
    if not node["class_type"].startswith("WebApp_"):
        return 10

    order = node["inputs"]["order"]
    if isinstance(order, int):
        return order
    else:
        # Link to another node. Follow until we get an int and increase by one.
        return get_order(workflow_dict, workflow_dict[order[0]]) + 1
