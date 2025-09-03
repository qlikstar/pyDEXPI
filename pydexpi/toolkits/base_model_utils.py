"""This module contains utility functions for pydexpi base models. Becasue these
are the common parents to the pydexpi classes, these are basic, overarching
functionalities for all dexpi classes."""

from pydexpi import dexpi_classes
from pydexpi.dexpi_classes.dexpiBaseModels import DexpiBaseModel, DexpiDataTypeBaseModel


def get_composition_attributes(dexpi_object: DexpiBaseModel) -> dict:
    """
    Retrieve attributes from a DEXPI object with the 'composition' attribute category.

    Parameters
    ----------
    dexpi_object : DexpiBaseModel
        An instance of a DEXPI model from which composition attributes are extracted.

    Returns
    -------
    dict
        A dictionary where the keys are field names and the values are the corresponding
        field values with the '"composition"' category."""
    return _get_attributes_with_category(dexpi_object, "composition")


def get_reference_attributes(dexpi_object: DexpiBaseModel) -> dict:
    """
    Retrieve attributes from a DEXPI object with the 'reference' attribute category.

    Parameters
    ----------
    dexpi_object : DexpiBaseModel
        An instance of a DEXPI model from which reference attributes are extracted.

    Returns
    -------
    dict
        A dictionary where the keys are field names and the values are the corresponding
        field values with the '"reference"' category."""
    return _get_attributes_with_category(dexpi_object, "reference")


def get_data_attributes(dexpi_object: DexpiBaseModel) -> dict:
    """
    Retrieve attributes from a DEXPI object with the 'data' attribute category.

    Parameters
    ----------
    dexpi_object : DexpiBaseModel
        An instance of a DEXPI model from which data attributes are extracted.

    Returns
    -------
    dict
        A dictionary where the keys are field names and the values are the corresponding
        field values with the '"data"' category."""
    return _get_attributes_with_category(dexpi_object, "data")


def _get_attributes_with_category(
    dexpi_object: DexpiBaseModel | DexpiDataTypeBaseModel, category: str
) -> dict:
    """
    Retrieve a dictionary of field names and their values from a dexpi_object
    based on the attribute_category annotation in the 'json_schema_extra'.

    This function iterates over the fields of the given dexpi_object,
    checks the 'json_schema_extra' metadata for a key '"attribute_category"',
    and includes the field in the output dictionary if its value matches the
    provided attribute category.

    Parameters
    ----------
    dexpi_object : DexpiBaseModel | DexpiDataTypeBaseModel
        A pydexpi object from which attributes are extracted.
    category : str
        The value of the '"attribute_category"' to filter the fields by.

    Returns
    -------
    dict
        A dictionary where the keys are field names and the values are the
        corresponding field values from the model, filtered by the given
        annotation.
    """

    attribute_dict = {}
    for fld_name, field in dexpi_object.__class__.model_fields.items():
        if field.json_schema_extra is not None:
            if "attribute_category" in field.json_schema_extra:
                if field.json_schema_extra["attribute_category"] == category:
                    attribute_dict[fld_name] = getattr(dexpi_object, fld_name)
    return attribute_dict


def get_dexpi_class(class_name: str) -> DexpiBaseModel:
    """
    Retrieve a DEXPI class by its name.

    Parameters
    ----------
    class_name : str
        The name of the DEXPI class to retrieve.

    Returns
    -------
    DexpiBaseModel
        The DEXPI class with the given name.
    """
    for submodule_name in dir(dexpi_classes):
        # Get the submodule dynamically
        submodule = getattr(dexpi_classes, submodule_name)
        cls = getattr(submodule, class_name, None)
        if cls:
            break
    else:
        raise AttributeError(f"Class {class_name} not a DEXPI class.")
    return cls


def get_dexpi_class_from_uri(uri: str) -> DexpiBaseModel:
    """
    Retrieve a DEXPI class from its URI.

    Parameters
    ----------
    uri : str
        The URI of the DEXPI class to retrieve.

    Returns
    -------
    DexpiBaseModel
        The DEXPI class corresponding to the given URI.
    """
    class_name = uri.split("/")[-1]

    # Strip .py from the back of the class name if it exists and capitalize first letter
    if class_name.endswith(".py"):
        class_name = class_name[:-3]
    class_name = class_name[0].upper() + class_name[1:]
    return get_dexpi_class(class_name)
