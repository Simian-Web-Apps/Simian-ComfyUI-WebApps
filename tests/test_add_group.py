"""Tests for the add_group function."""

import pytest
from simian.gui import component, component_properties

from simian.comfy import add_group

ID = "28"


def test_new_column():
    """Test the column option."""
    cont = component.Container("test")
    new_comp = wrap_add_group("Column", parent=cont)

    # Check that we get a Column component in a Columns group component.
    assert isinstance(new_comp, component_properties.Column)
    # Column does not have a key.

    # Check that it is a new Column group component.
    assert isinstance(cont.components[0], component.Columns)
    assert ID in cont.components[0].key


def test_column_reuse():
    """Test the column option."""
    cont = component.Container("test")
    cols = component.Columns("cols", cont)
    cols.setContent([[], []], [9, 3])
    component.Number("nr", cont)

    new_comp = wrap_add_group("Column", parent=cont)

    # Check that we get a Column component in a Columns group component.
    assert isinstance(new_comp, component_properties.Column)
    # Column does not have a key.

    # Check that the tab was added to an existing Columns group component.
    assert len(cols.columns) == 3
    assert cols.columns[-1] == new_comp


def test_panel():
    """Test the Section option."""
    extra_inputs = {"collapsible": True}

    new_comp = wrap_add_group("Section", extra_inputs)

    assert isinstance(new_comp, component.Panel)


def test_new_tab():
    """Test the tab option."""
    cont = component.Container("test")
    new_comp = wrap_add_group("Tab", parent=cont)

    # Check that we get a Tab component in a Tabs group component.
    assert isinstance(new_comp, component_properties.Tab)
    assert ID in new_comp.key

    # Check that it is a new Tabs group component.
    assert isinstance(cont.components[0], component.Tabs)
    assert ID in cont.components[0].key


def test_tab_reuse():
    """Test the tab option, but now with the parent already containing a Tabs group."""
    cont = component.Container("test")
    tabs = component.Tabs("tabs", cont)
    tabs.addTab(label="One", key="one")
    tabs.addTab(label="Two", key="two")
    component.Number("nr", cont)

    new_comp = wrap_add_group("Tab", parent=cont)

    assert isinstance(new_comp, component_properties.Tab)
    assert ID in new_comp.key

    # Check that the tab was added to an existing Tabs group component.
    assert len(tabs.components) == 3
    assert tabs.components[-1] == new_comp


def test_error():
    """Add_group should throw an error for unknown types."""
    with pytest.raises(ValueError):
        wrap_add_group("NotExisting", {})


def wrap_add_group(type_str: str, inputs: dict = dict(), parent: component.Component = None):
    if parent is None:
        parent = component.Container("test")

    group_dict = {
        "inputs": {"order": 11, "Advanced": False, "mode": type_str, **inputs},
        "class_type": "WebApp_Grouping",
        "_meta": {"title": "Coordinates"},
        "id": ID,
    }

    return add_group(type_str, group_dict, parent)


if __name__ == "__main__":
    pytest.main()
