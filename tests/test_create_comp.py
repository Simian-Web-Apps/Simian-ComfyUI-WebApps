"""Tests for the create_comp function."""

from simian.gui import component, component_properties
from simian.comfy import create_comp
import pytest


ID = "28"


def test_description():
    """Test the Description node."""
    inputs = {"description": "Test"}

    comp = wrap_create_comp("WebApp_Description", inputs)

    assert isinstance(comp, component.HtmlElement)
    assert comp.content == "Test"


def test_description_fail():
    """Description node must have a description input."""
    with pytest.raises(KeyError):
        wrap_create_comp("WebApp_Description")


def test_integer_input():
    """Test the integer input"""
    inputs = {
        "minimum": 2,
        "maximum": 5,
        "default": 3,
    }

    comp = wrap_create_comp("WebApp_Integerinput", inputs)
    assert isinstance(comp, component.Number)
    assert isinstance(comp.validate, component_properties.Validate)
    assert comp.decimalLimit == 0


def test_float_input():
    """Test floating point input."""
    comp = wrap_create_comp("WebApp_Floatinput", {"default": 2.1})
    assert isinstance(comp, component.Number)
    assert comp.decimalLimit != 0


def test_boolean():
    """Test boolean input."""
    comp = wrap_create_comp("WebApp_BooleanInput", {"default": False})
    assert isinstance(comp, component.Checkbox)


def test_string_input():
    """Test singleline string."""
    inputs = {"default": "test", "mode": "Singleline"}
    comp = wrap_create_comp("WebApp_Stringinput", inputs)
    assert isinstance(comp, component.TextField)


def test_multiline_string_input():
    """Test singleline string."""
    inputs = {"default": "test", "mode": "Multiline"}
    comp = wrap_create_comp("WebApp_Stringinput", inputs)
    assert isinstance(comp, component.TextArea)


def test_selection_input():
    """Test Selection input."""
    inputs = {
        "default": "B",
        "options": ["A", "B", "C"],
        "full_options": [1, 2, 3],
    }
    comp = wrap_create_comp("WebApp_Selectioninput", inputs)

    assert isinstance(comp, component.Select)
    assert not comp.multiple


def test_selection_input_2():
    """Test Selection input with some alternative inputs."""
    inputs = {
        "default": "C",
        "options": ["A", "B", "C"],
        "maximum": 3,
    }
    comp = wrap_create_comp("WebApp_Selectioninput", inputs)

    assert isinstance(comp, component.Select)
    assert comp.multiple


def test_image_input():
    """Test the create image input."""
    component.Component._init_config(["mode", "local"], ["portalCache", True])
    inputs = {"is_image_used": True, "is_mask_used": True}

    comp = wrap_create_comp("WebApp_MaskedImageinput", inputs)

    assert isinstance(comp, component.Panel)


def wrap_create_comp(type_str: str, inputs: dict = dict()):
    node_dict = {
        "inputs": {"order": 11, "Advanced": False, **inputs},
        "class_type": type_str,
        "_meta": {"title": "Coordinates"},
        "id": ID,
    }

    return create_comp(node_dict)


if __name__ == "__main__":
    pytest.main()
