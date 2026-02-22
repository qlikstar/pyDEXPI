from pathlib import Path

from pydexpi.dexpi_classes.pydantic_classes import DexpiModel
from pydexpi.loaders.proteus_serializer.core import ParserFactoryProtocol, ProteusLoader
from pydexpi.loaders.proteus_serializer.parser_factory import ParserFactory
from pydexpi.loaders.proteus_serializer.xml_writer import ProteusXMLWriter
from pydexpi.loaders.serializer import Serializer


class ProteusSerializer(Serializer):
    """Main class for the Proteus Serializer that implements the Serializer interface."""

    def __init__(self, parser_factory: ParserFactoryProtocol = None):
        """Initialize the ProteusSerializer with a parser factory.

        Parameters
        ----------
        parser_factory : ParserFactoryProtocol, optional
            A factory to create parsers for the ProteusLoader. If not provided, a default
            ParserFactory instance will be used.
        """

        parser_factory = parser_factory or ParserFactory()
        self.proteus_loader = ProteusLoader(parser_factory)
        self.xml_writer = ProteusXMLWriter()

    def save(self, model: DexpiModel, dir_path: Path, filename: str):
        """Saves a DEXPI model to an XML file in Proteus format.

        Parameters
        ----------
        model : DexpiModel
            DEXPI model that should be saved.
        dir_path : Path
            Directory where the DEXPI model should be saved.
        filename : str
            Filename for the saved DEXPI model.
        """
        if not filename.endswith(".xml"):
            filename += ".xml"
        path = Path(dir_path) / filename

        self.xml_writer.write_to_file(model, path)

    def load(self, dir_path: Path, filename: str) -> DexpiModel:
        """Loads a DEXPI model from a file using the ProteusLoader.

        Parameters
        ----------
        dir_path : Path
            The directory path where the file is located.
        filename : str
            The name of the file to load.

        Returns
        -------
        DexpiModel
            The loaded DEXPI model."""

        if not filename.endswith(".xml"):
            filename += ".xml"
        path = Path(dir_path) / filename

        return self.proteus_loader.load_xml_file(path)
