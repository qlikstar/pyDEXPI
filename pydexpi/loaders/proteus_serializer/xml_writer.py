"""XML Writer module for serializing DEXPI models to Proteus XML format.

This module provides functionality to convert DEXPI model objects back into
Proteus XML format, enabling round-trip serialization (load and save).
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydexpi.dexpi_classes.pydantic_classes import DexpiBaseModel, DexpiDataTypeBaseModel, DexpiModel
from pydexpi.toolkits.base_model_utils import (
    get_composition_attributes,
    get_data_attributes,
    get_reference_attributes,
)


class ProteusXMLWriter:
    """Writer class for converting DEXPI models to Proteus XML format."""

    def __init__(self):
        """Initialize the XML writer."""
        self.id_map = {}

    def write_to_file(self, model: DexpiModel, file_path: Path) -> None:
        """Write a DEXPI model to an XML file in Proteus format.

        Parameters
        ----------
        model : DexpiModel
            The DEXPI model to serialize
        file_path : Path
            The path where the XML file should be written
        """
        root = self._create_plant_model_element(model)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(file_path, encoding="UTF-8", xml_declaration=True)

    def _create_plant_model_element(self, model: DexpiModel) -> ET.Element:
        """Create the root PlantModel XML element from a DexpiModel.

        Parameters
        ----------
        model : DexpiModel
            The DEXPI model to convert

        Returns
        -------
        ET.Element
            The root PlantModel XML element
        """
        root = ET.Element("PlantModel")
        
        # Add PlantInformation element
        plant_info = ET.SubElement(root, "PlantInformation")
        plant_info.set("Application", "pyDEXPI")
        plant_info.set("ApplicationVersion", "1.3")
        
        if model.exportDateTime:
            date_str = model.exportDateTime.strftime("%Y-%m-%d")
            time_str = model.exportDateTime.strftime("%H:%M:%S.%f")
            plant_info.set("Date", date_str)
            plant_info.set("Time", time_str)
        else:
            now = datetime.now()
            plant_info.set("Date", now.strftime("%Y-%m-%d"))
            plant_info.set("Time", now.strftime("%H:%M:%S.%f"))
        
        plant_info.set("Discipline", "PID")
        plant_info.set("Is3D", "no")
        
        if model.originatingSystemName:
            plant_info.set("OriginatingSystem", model.originatingSystemName)
        else:
            plant_info.set("OriginatingSystem", "pyDEXPI")
        
        if model.originatingSystemVendorName:
            plant_info.set("OriginatingSystemVendor", model.originatingSystemVendorName)
        else:
            plant_info.set("OriginatingSystemVendor", "Process Intelligence Research")
        
        if model.originatingSystemVersion:
            plant_info.set("OriginatingSystemVersion", model.originatingSystemVersion)
        else:
            plant_info.set("OriginatingSystemVersion", "1.0")
        
        plant_info.set("SchemaVersion", "4.1.1")
        plant_info.set("Units", "mm")
        
        # Add UnitsOfMeasure sub-element
        ET.SubElement(plant_info, "UnitsOfMeasure")
        
        # Process conceptual model if present
        if model.conceptualModel:
            self._add_conceptual_model_elements(root, model.conceptualModel)
        
        # Process diagram if present
        if model.diagram:
            self._add_element_from_dexpi_object(root, model.diagram)
        
        # Process shape catalogues if present
        for catalogue in model.shapeCatalogues:
            self._add_element_from_dexpi_object(root, catalogue)
        
        return root

    def _add_conceptual_model_elements(self, parent: ET.Element, conceptual_model: Any) -> None:
        """Add elements from the conceptual model to the parent element.

        Parameters
        ----------
        parent : ET.Element
            The parent XML element
        conceptual_model : ConceptualModel
            The conceptual model containing the engineering data
        """
        # Add MetaData first if present
        if conceptual_model.metaData:
            self._add_element_from_dexpi_object(parent, conceptual_model.metaData)
        
        # Add ActuatingSystems
        for actuating_system in conceptual_model.actuatingSystems:
            self._add_element_from_dexpi_object(parent, actuating_system)
        
        # Add InstrumentationLoopFunctions
        for loop_function in conceptual_model.instrumentationLoopFunctions:
            self._add_element_from_dexpi_object(parent, loop_function)
        
        # Add PipingNetworkSystems
        for piping_system in conceptual_model.pipingNetworkSystems:
            self._add_element_from_dexpi_object(parent, piping_system)
        
        # Add ProcessInstrumentationFunctions
        for instrument_function in conceptual_model.processInstrumentationFunctions:
            self._add_element_from_dexpi_object(parent, instrument_function)
        
        # Add SignalLineSystems
        for signal_line in conceptual_model.signalLineSystems:
            self._add_element_from_dexpi_object(parent, signal_line)
        
        # Add TaggedPlantItems
        for plant_item in conceptual_model.taggedPlantItems:
            self._add_element_from_dexpi_object(parent, plant_item)

    def _add_element_from_dexpi_object(self, parent: ET.Element, obj: DexpiBaseModel) -> ET.Element:
        """Create and add an XML element from a DEXPI object.

        Parameters
        ----------
        parent : ET.Element
            The parent XML element
        obj : DexpiBaseModel
            The DEXPI object to convert

        Returns
        -------
        ET.Element
            The created XML element
        """
        # Get the class name for the element tag
        class_name = obj.__class__.__name__
        element = ET.SubElement(parent, class_name)
        
        # Add ID attribute
        element.set("ID", obj.id)
        
        # Add ComponentClass and ComponentClassURI if available
        element.set("ComponentClass", class_name)
        if hasattr(obj, 'uri') and obj.uri:
            # Convert pyDEXPI URI to DEXPI RDL URI
            rdl_uri = f"http://sandbox.dexpi.org/rdl/{class_name}"
            element.set("ComponentClassURI", rdl_uri)
        
        # Process data attributes first
        data_attrs = get_data_attributes(obj)
        self._add_data_attributes(element, obj, data_attrs)
        
        # Process composition attributes
        comp_attrs = get_composition_attributes(obj)
        self._add_composition_attributes(element, comp_attrs)
        
        # Process reference attributes
        ref_attrs = get_reference_attributes(obj)
        self._add_reference_attributes(element, ref_attrs)
        
        return element

    def _add_data_attributes(self, element: ET.Element, obj: DexpiBaseModel, data_attrs: dict) -> None:
        """Add data attributes to an XML element.

        Parameters
        ----------
        element : ET.Element
            The XML element to add attributes to
        obj : DexpiBaseModel
            The source DEXPI object
        data_attrs : dict
            Dictionary of data attributes
        """
        generic_attrs = []
        
        for attr_name, attr_value in data_attrs.items():
            if attr_value is None:
                continue
            
            # Handle special attributes that go directly as XML attributes
            if attr_name in ['tagName', 'componentName', 'label']:
                if isinstance(attr_value, str):
                    # Convert camelCase to PascalCase for attribute names
                    xml_attr_name = attr_name[0].upper() + attr_name[1:]
                    element.set(xml_attr_name, attr_value)
            # Handle data type objects
            elif isinstance(attr_value, DexpiDataTypeBaseModel):
                self._add_data_type_element(element, attr_name, attr_value)
            # Handle primitive types
            elif isinstance(attr_value, (str, int, float, bool, Decimal)):
                generic_attrs.append((attr_name, attr_value))
            elif isinstance(attr_value, datetime):
                generic_attrs.append((attr_name, attr_value.isoformat()))
        
        # Add GenericAttributes if any
        if generic_attrs:
            self._add_generic_attributes_element(element, generic_attrs)

    def _add_data_type_element(self, parent: ET.Element, attr_name: str, data_type_obj: DexpiDataTypeBaseModel) -> None:
        """Add a data type object as an XML element.

        Parameters
        ----------
        parent : ET.Element
            The parent XML element
        attr_name : str
            The attribute name
        data_type_obj : DexpiDataTypeBaseModel
            The data type object to add
        """
        class_name = data_type_obj.__class__.__name__
        element = ET.SubElement(parent, class_name)
        
        # Add all fields of the data type
        for field_name, field_value in data_type_obj.model_dump().items():
            if field_value is not None:
                if isinstance(field_value, (str, int, float, bool)):
                    # Convert camelCase to PascalCase
                    xml_attr_name = field_name[0].upper() + field_name[1:]
                    element.set(xml_attr_name, str(field_value))
                elif isinstance(field_value, Decimal):
                    xml_attr_name = field_name[0].upper() + field_name[1:]
                    element.set(xml_attr_name, str(field_value))

    def _add_generic_attributes_element(self, parent: ET.Element, attrs: list) -> None:
        """Add a GenericAttributes element with GenericAttribute children.

        Parameters
        ----------
        parent : ET.Element
            The parent XML element
        attrs : list
            List of tuples (name, value) for generic attributes
        """
        if not attrs:
            return
        
        generic_attrs_elem = ET.SubElement(parent, "GenericAttributes")
        generic_attrs_elem.set("Set", "DexpiAttributes")
        generic_attrs_elem.set("Number", str(len(attrs)))
        
        for attr_name, attr_value in attrs:
            attr_elem = ET.SubElement(generic_attrs_elem, "GenericAttribute")
            
            # Convert camelCase to proper attribute name
            display_name = attr_name[0].upper() + attr_name[1:] + "AssignmentClass"
            attr_elem.set("Name", display_name)
            attr_elem.set("AttributeURI", f"http://sandbox.dexpi.org/rdl/{display_name}")
            
            # Determine format
            if isinstance(attr_value, bool):
                attr_elem.set("Format", "boolean")
                attr_elem.set("Value", str(attr_value).lower())
            elif isinstance(attr_value, int):
                attr_elem.set("Format", "integer")
                attr_elem.set("Value", str(attr_value))
            elif isinstance(attr_value, (float, Decimal)):
                attr_elem.set("Format", "double")
                attr_elem.set("Value", str(attr_value))
            else:
                attr_elem.set("Format", "string")
                attr_elem.set("Value", str(attr_value))

    def _add_composition_attributes(self, parent: ET.Element, comp_attrs: dict) -> None:
        """Add composition attributes as child elements.

        Parameters
        ----------
        parent : ET.Element
            The parent XML element
        comp_attrs : dict
            Dictionary of composition attributes
        """
        for attr_name, attr_value in comp_attrs.items():
            if attr_value is None:
                continue
            
            # Handle lists of objects
            if isinstance(attr_value, list):
                for item in attr_value:
                    if isinstance(item, DexpiBaseModel):
                        self._add_element_from_dexpi_object(parent, item)
            # Handle single objects
            elif isinstance(attr_value, DexpiBaseModel):
                self._add_element_from_dexpi_object(parent, attr_value)

    def _add_reference_attributes(self, element: ET.Element, ref_attrs: dict) -> None:
        """Add reference attributes as Association elements.

        Parameters
        ----------
        element : ET.Element
            The XML element to add associations to
        ref_attrs : dict
            Dictionary of reference attributes
        """
        for attr_name, attr_value in ref_attrs.items():
            if attr_value is None:
                continue
            
            # Handle lists of references
            if isinstance(attr_value, list):
                for item in attr_value:
                    if isinstance(item, DexpiBaseModel):
                        assoc = ET.SubElement(element, "Association")
                        assoc.set("Type", attr_name)
                        assoc.set("ItemID", item.id)
            # Handle single references
            elif isinstance(attr_value, DexpiBaseModel):
                assoc = ET.SubElement(element, "Association")
                assoc.set("Type", attr_name)
                assoc.set("ItemID", attr_value.id)
