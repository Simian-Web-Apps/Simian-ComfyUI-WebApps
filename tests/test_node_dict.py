"""Tests for the node_dict_to_component function."""

from simian.gui import component

from simian.comfy import node_dict_to_component

ID = "28"


def _create_node_dict(node_type_str: str, id: str, inputs: dict = dict()):
    return {
        "inputs": {"order": 11, "Advanced": False, **inputs},
        "class_type": node_type_str,
        "_meta": {"title": "Coordinates"},
        "id": id,
    }


ALL_NODES = {
    ID: [
        _create_node_dict("WebApp_Description", "23", {"description": "test"}),
        _create_node_dict("WebApp_Integerinput", "27", {"default": 4}),
    ],
    "sth_else": [_create_node_dict("NotExisting", "error")],
}


def test_one_node():
    """Test adding a simple component."""
    parent = component.Container("test")
    wrap_node_dict("WebApp_Description", {"description": "test"}, parent)
    assert len(parent.components) == 1


def test_grouped_node():
    """Create a Tab with contents."""
    parent = component.Container("test")
    wrap_node_dict("WebApp_Grouping", {"mode": "Tab"}, parent)

    # Check that a Tabs group component was added and that it contains a tab with the two controls we are expecting
    assert len(parent.components) == 1
    assert isinstance(parent.components[0], component.Tabs)
    assert len(parent.components[0].components[0].components) == len(ALL_NODES[ID])


def test_repeating():
    """Create a Tab with contents."""
    parent = component.Container("test")
    wrap_node_dict(
        "WebApp_Grouping", {"mode": "Repeating", "mode.minimum": 2, "mode.maximum": 3}, parent
    )

    # Check that a Tabs group component was added and that it contains a tab with the two controls we are expecting
    assert len(parent.components) == 1
    assert isinstance(parent.components[0], component.DataGrid)
    assert len(parent.components[0].components) == len(ALL_NODES[ID])


def wrap_node_dict(node_type_str: str, inputs: dict = dict(), parent: component.Component = None):
    """Util"""
    if parent is None:
        parent = component.Container("test")

    node_dict = _create_node_dict(node_type_str, ID, inputs)

    return node_dict_to_component(ALL_NODES, node_dict, level=0, parent=parent)
