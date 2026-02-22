"""Tests for ProteusSerializer XML save functionality."""

from decimal import Decimal
from pathlib import Path

import pytest

from pydexpi.dexpi_classes import dexpiModel, equipment, physicalQuantities
from pydexpi.loaders import ProteusSerializer
from pydexpi.toolkits import model_toolkit as mt


@pytest.fixture
def simple_reactor_model():
    """Creates a simple reactor DEXPI model for testing.

    Returns
    -------
    DexpiModel
        A simple DEXPI model with a reactor.
    """
    return dexpiModel.DexpiModel(
        conceptualModel=dexpiModel.ConceptualModel(
            taggedPlantItems=[
                equipment.PressureVessel(
                    tagName="R-1",
                    chambers=[
                        equipment.Chamber(
                            upperLimitDesignPressure=physicalQuantities.PressureGauge(
                                unit=physicalQuantities.PressureGaugeUnit("bar"),
                                value=Decimal(1),
                            )
                        )
                    ],
                )
            ]
        )
    )


def test_proteus_serializer_save_simple_model(simple_reactor_model, tmp_path):
    """Test saving a simple DEXPI model to XML format.

    Parameters
    ----------
    simple_reactor_model : DexpiModel
        Simple reactor model fixture.
    tmp_path : Path
        Temporary directory for test files.
    """
    serializer = ProteusSerializer()
    output_file = "test_reactor"
    
    serializer.save(simple_reactor_model, tmp_path, output_file)
    
    saved_file = tmp_path / "test_reactor.xml"
    assert saved_file.exists()
    
    with open(saved_file) as f:
        content = f.read()
        assert '<?xml version' in content
        assert '<PlantModel>' in content
        assert '<PressureVessel' in content
        assert 'R-1' in content


def test_proteus_serializer_roundtrip_simple_model(simple_reactor_model, tmp_path):
    """Test save and load roundtrip for a simple DEXPI model.

    Parameters
    ----------
    simple_reactor_model : DexpiModel
        Simple reactor model fixture.
    tmp_path : Path
        Temporary directory for test files.
    """
    serializer = ProteusSerializer()
    output_file = "test_roundtrip"
    
    serializer.save(simple_reactor_model, tmp_path, output_file)
    loaded_model = serializer.load(tmp_path, output_file)
    
    assert loaded_model is not None
    assert loaded_model.conceptualModel is not None
    assert len(loaded_model.conceptualModel.taggedPlantItems) == 1
    
    original_item = simple_reactor_model.conceptualModel.taggedPlantItems[0]
    loaded_item = loaded_model.conceptualModel.taggedPlantItems[0]
    
    assert loaded_item.__class__.__name__ == "PressureVessel"
    assert loaded_item.tagName == original_item.tagName


def test_proteus_serializer_roundtrip_complex_model(loaded_example_dexpi, tmp_path):
    """Test save and load roundtrip for the complex example DEXPI model.

    Parameters
    ----------
    loaded_example_dexpi : DexpiModel
        The loaded example DEXPI model from conftest.
    tmp_path : Path
        Temporary directory for test files.
    """
    serializer = ProteusSerializer()
    output_file = "test_complex_roundtrip"
    
    original_model = loaded_example_dexpi
    original_item_count = len(mt.get_all_instances_in_model(original_model))
    
    serializer.save(original_model, tmp_path, output_file)
    loaded_model = serializer.load(tmp_path, output_file)
    
    assert loaded_model is not None
    assert loaded_model.conceptualModel is not None
    
    loaded_item_count = len(mt.get_all_instances_in_model(loaded_model))
    
    assert len(loaded_model.conceptualModel.actuatingSystems) == len(
        original_model.conceptualModel.actuatingSystems
    )
    assert len(loaded_model.conceptualModel.taggedPlantItems) == len(
        original_model.conceptualModel.taggedPlantItems
    )
    assert len(loaded_model.conceptualModel.pipingNetworkSystems) == len(
        original_model.conceptualModel.pipingNetworkSystems
    )


def test_proteus_serializer_save_with_xml_extension(simple_reactor_model, tmp_path):
    """Test that .xml extension is added automatically if not provided.

    Parameters
    ----------
    simple_reactor_model : DexpiModel
        Simple reactor model fixture.
    tmp_path : Path
        Temporary directory for test files.
    """
    serializer = ProteusSerializer()
    
    serializer.save(simple_reactor_model, tmp_path, "test_no_extension")
    assert (tmp_path / "test_no_extension.xml").exists()
    
    serializer.save(simple_reactor_model, tmp_path, "test_with_extension.xml")
    assert (tmp_path / "test_with_extension.xml").exists()


def test_proteus_serializer_save_creates_valid_xml(simple_reactor_model, tmp_path):
    """Test that saved XML is valid and parseable.

    Parameters
    ----------
    simple_reactor_model : DexpiModel
        Simple reactor model fixture.
    tmp_path : Path
        Temporary directory for test files.
    """
    import xml.etree.ElementTree as ET
    
    serializer = ProteusSerializer()
    output_file = "test_valid_xml"
    
    serializer.save(simple_reactor_model, tmp_path, output_file)
    
    saved_file = tmp_path / "test_valid_xml.xml"
    tree = ET.parse(saved_file)
    root = tree.getroot()
    
    assert root.tag == "PlantModel"
    
    plant_info = root.find("PlantInformation")
    assert plant_info is not None
    assert plant_info.get("Application") == "pyDEXPI"
    assert plant_info.get("SchemaVersion") == "4.1.1"
