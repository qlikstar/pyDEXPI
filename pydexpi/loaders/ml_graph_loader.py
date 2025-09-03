import warnings
from copy import copy

import networkx as nx
import plotly.graph_objects as go
from Flowsheet_Class.utils_visualization import _add_positions
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from networkx import DiGraph

from pydexpi.dexpi_classes import equipment, instrumentation, piping
from pydexpi.dexpi_classes.dexpiBaseModels import DexpiBaseModel
from pydexpi.dexpi_classes.dexpiModel import DexpiModel
from pydexpi.loaders.graph_loader import NXGraphLoader
from pydexpi.toolkits.base_model_utils import (
    get_data_attributes,
    get_dexpi_class,
)


class MLGraphLoader(NXGraphLoader):
    """Loads a DEXPI model instance into networkX graph. The graph is optimized
    for machine learning tasks.

    Attributes
    ----------
        plant_graph (nx.DiGraph): Graph version of a plant.
        plant_model (DexpiModel): Instance of DexpiModel.


    """

    def __init__(
        self,
        plant_graph: DiGraph | None = None,
        plant_model: DexpiModel | None = None,
    ):
        """Initializes a new instance of GraphLoader.

        Args:
        ----
            plant_graph (Optional[DiGraph]): Initialize loader with the graph
                version of a plant. Defaults to an empty graph if not provided.
            plant_model (Optional[PlantModel]): Initialize loader with an
                instance of PlantModel. Defaults to a new instance if not
                provided.

        """
        self.plant_graph = plant_graph if plant_graph is not None else DiGraph()
        self.plant_model = plant_model if plant_model is not None else DexpiModel()

    # Implement abstract methods
    def dexpi_to_graph(self, dexpi_model: DexpiModel) -> DiGraph:
        """
        Parse a pyDEXPI model into a NetworkX graph representation.

        Parameters
        ----------
        pydexpi_model : DexpiModel
            The pyDEXPI model to be parsed into a NetworkX graph.

        Returns
        -------
        nx.Graph
            The parsed NetworkX graph representation of the pyDEXPI model.
        """
        # Reset plant graph and set dexpi model
        self.plant_graph = DiGraph()
        self.plant_model = dexpi_model

        self.parse_equipment_and_piping()
        self.parse_instrumentation()

        return self.plant_graph

    def graph_to_dexpi(self, plant_graph: DiGraph) -> DexpiModel:
        """Parsing the example graph back to pyDEXPI is not supported yet."""
        raise NotImplementedError

    def validate_graph_format(
        self, special_node_attributes: list[str] = [], special_edge_attributes: list[str] = []
    ):
        """Validate a graph against the graph format. Raises an AttributeError if the graph is not valid.

        Parameters
        ----------
        special_node_attributes : list[str]
            Node attributes besides "dexpi_class" and besides attributes of a DEXPI class.
        special_edge_attributes : list[str]
            Edge attributes besides "dexpi_class" and besides attributes of a DEXPI class.
        """
        special_node_attributes = special_node_attributes + ["dexpi_class", "id"]
        special_edge_attributes = special_edge_attributes + ["dexpi_class"]

        for node_attributes in self.plant_graph.nodes.values():
            self.validate_node(node_attributes, special_node_attributes)
        for (source, target), edge_attributes in self.plant_graph.edges.items():
            source_class_name = self.plant_graph.nodes[source]["dexpi_class"]
            target_class_name = self.plant_graph.nodes[target]["dexpi_class"]
            self.validate_edge(
                source_class_name, target_class_name, edge_attributes, special_edge_attributes
            )

    def validate_node(self, node: dict, special_node_attributes: list[str] = []):
        """Validate a node against the DEXPI class and its attributes.

        Parameters
        ----------
        node : dict
            Dictionary describing the node.
        special_node_attributes : list[str]
            Node attributes besides "dexpi_class" and besides attributes of a DEXPI class.
        """
        node_class = get_dexpi_class(node["dexpi_class"])
        self.validate_node_classes(node_class)
        self.validate_node_attributes(node, node_class, special_node_attributes)

    def validate_node_classes(self, node_class: type[DexpiBaseModel]):
        """Validate the node class name against the allowed node classes.
        The following classes are allowed as nodes:
        - NozzleOwner
        - PipingNetworkSegmentItem
        - ProcessInstrumentationFunction
        - SignalOffPageConnector
        - ControlledActuator
        - Positioner
        - ElectronicFrequencyConverter
        - OfflinePrimaryElement

        Parameters
        ----------
        node_class : type[DexpiBaseModel]
            Class to be validated.

        Raises
        ------
        AttributeError
            Node class is not valid.
        """
        node_classes = (
            equipment.NozzleOwner
            | piping.PipingNetworkSegmentItem
            | instrumentation.ProcessInstrumentationFunction
            | instrumentation.SignalOffPageConnector
            | instrumentation.ControlledActuator
            | instrumentation.Positioner
            | instrumentation.ElectronicFrequencyConverter
            | instrumentation.OfflinePrimaryElement
        )
        if not issubclass(node_class, node_classes):
            raise AttributeError(f"'{node_class.__name__}' not a valid DEXPI class or node.")

    def validate_node_attributes(
        self, node: dict, node_class: type[DexpiBaseModel], special_node_attributes: list[str] = []
    ):
        """Validate attributes of a node against the DEXPI class and its allowed attributes.

        Parameters
        ----------
        node : dict
            Attributes of the node.
        node_class : type[DexpiBaseModel]
            Class of the node.
        special_node_attributes : list[str]
            Node attributes besides "dexpi_class" and besides attributes of a DEXPI class.

        Raises
        ------
        AttributeError
            Node attributes are not valid.
        """
        for attribute in node:
            if attribute not in (list(node_class.model_fields) + special_node_attributes):
                raise AttributeError(
                    f"Attribute {attribute} not valid for DEXPI class {node['dexpi_class']}."
                )

    def validate_edge(
        self,
        source_class_name: str,
        target_class_name: str,
        edge: dict,
        special_edge_attributes: list[str] = [],
    ):
        """The following classes are allowed as edges:
        - PipingConnection
        - SignalConveyingFunction
        - OperatedValveReference
        - ElectronicFrequencyConverter


        Parameters
        ----------
        source_class_name : str
            Dexpi class name of the source node.
        target_class_name : str
            Dexpi class name of the target node.
        edge : dict
            Attributes of the edge.
        special_edge_attributes : list[str]
            Edge attributes besides "dexpi_class" and besides attributes of a DEXPI class.
        """
        edge_class = get_dexpi_class(edge["dexpi_class"])
        self.validate_edge_classes(edge_class)
        self.validate_edge_attributes(edge, edge_class, special_edge_attributes)
        source_class = get_dexpi_class(source_class_name)
        self.validate_edge_sources(source_class, edge_class)
        target_class = get_dexpi_class(target_class_name)
        self.validate_edge_targets(target_class, edge_class)

    def validate_edge_classes(self, edge_class: type[DexpiBaseModel]):
        """Validate the edge class name against the allowed edge classes.

        Parameters
        ----------
        edge_class : type[DexpiBaseModel]
            Edge class to be validated.

        Raises
        ------
        AttributeError
            If the edge class is not valid.
        """
        edge_classes = (
            piping.PipingConnection
            | instrumentation.SignalConveyingFunction
            | instrumentation.OperatedValveReference
            | instrumentation.ElectronicFrequencyConverter
        )
        if not issubclass(edge_class, edge_classes):
            raise AttributeError(f"'{edge_class.__name__}' not a valid DEXPI class or edge.")

    def validate_edge_attributes(
        self, edge: dict, edge_class: type[DexpiBaseModel], special_edge_attributes: list[str] = []
    ):
        """Validate the attributes of an edge against the DEXPI class and its allowed attributes.

        Parameters
        ----------
        edge : dict
            Attributes of the edge.
        edge_class : type[DexpiBaseModel]
            Class of the edge.
        special_edge_attributes : list[str]
            Edge attributes besides "dexpi_class" and besides attributes of a DEXPI class.

        Raises
        ------
        AttributeError
            Edge attributes are not valid.
        """
        valid_attributes = copy(edge_class.model_fields)
        # Special handling for PipingConnection
        if issubclass(edge_class, piping.PipingConnection):
            valid_attributes.update(piping.PipingNetworkSegment.model_fields)

        for key in edge.keys():
            if key not in (list(valid_attributes) + special_edge_attributes):
                raise AttributeError(
                    f"Attribute {key} not valid for DEXPI class {edge['dexpi_class']}."
                )

    def validate_edge_sources(
        self, source_class: type[DexpiBaseModel], edge_class: type[DexpiBaseModel]
    ):
        """Validates if the source node is allowed to be connected to the edge.

        Parameters
        ----------
        source_class : type[DexpiBaseModel]
            Source node class.
        edge_class : type[DexpiBaseModel]
            Edge class.

        Raises
        ------
        AttributeError
            Edge source is not valid.
        """
        if issubclass(edge_class, piping.PipingConnection):
            if not issubclass(
                source_class,
                (equipment.NozzleOwner | piping.PipingNetworkSegmentItem),
            ):
                raise AttributeError(
                    f"Source of {edge_class.__name__} must be NozzleOwner or PipingNetworkSegmentItem."
                )

        elif issubclass(edge_class, instrumentation.SignalConveyingFunction):
            if not issubclass(
                source_class,
                (
                    equipment.NozzleOwner
                    | piping.PipingNetworkSegmentItem
                    | instrumentation.ProcessInstrumentationFunction
                    | instrumentation.SignalOffPageConnector
                    | instrumentation.OfflinePrimaryElement
                ),
            ):
                raise AttributeError(
                    f"Source of {edge_class.__name__} should be connected to at least one instrumentation object."
                )

        elif issubclass(edge_class, instrumentation.OperatedValveReference):
            if not issubclass(
                source_class, (instrumentation.ControlledActuator | instrumentation.Positioner)
            ):
                raise AttributeError(
                    f"Source of {edge_class.__name__} should connect ControlledActuator or Positioner to (subclass of) OperatedValve."
                )

        elif issubclass(edge_class, instrumentation.ElectronicFrequencyConverter):
            if not issubclass(source_class, instrumentation.ProcessInstrumentationFunction):
                raise AttributeError(
                    f"Source of {edge_class.__name__} must be ProcessInstrumentationFunction."
                )

    def validate_edge_targets(
        self, target_class: type[DexpiBaseModel], edge_class: type[DexpiBaseModel]
    ):
        """Validates if the target node is allowed to be connected to the edge.

        Parameters
        ----------
        target_class : type[DexpiBaseModel]
            Target node of the edge.
        edge_class : type[DexpiBaseModel]
            Edge class.

        Raises
        ------
        AttributeError
            Edge target is not valid.
        """
        if issubclass(edge_class, piping.PipingConnection):
            if not issubclass(
                target_class,
                (equipment.NozzleOwner | piping.PipingNetworkSegmentItem),
            ):
                raise AttributeError(
                    f"Target of {edge_class.__name__} must be NozzleOwner or PipingNetworkSegmentItem."
                )

        elif issubclass(edge_class, instrumentation.SignalConveyingFunction):
            if not issubclass(
                target_class,
                (
                    instrumentation.ProcessInstrumentationFunction
                    | instrumentation.ControlledActuator
                    | instrumentation.Positioner
                    | equipment.Equipment  # assume that SignalConveyingFunction has target ActuatingElectricalFunction which has a Nozzle of an Equipment as SensingLocation
                ),
            ):
                raise AttributeError(
                    f"Target of {edge_class.__name__} must be ProcessInstrumentationFunction, ControlledActuator, or Positioner."
                )

        elif issubclass(edge_class, instrumentation.OperatedValveReference):
            if not issubclass(target_class, piping.OperatedValve):
                raise AttributeError(
                    f"Target of {edge_class.__name__} must be (subclass of) OperatedValve."
                )

        elif issubclass(edge_class, instrumentation.ElectronicFrequencyConverter):
            if not issubclass(target_class, instrumentation.ElectronicFrequencyConverter):
                raise AttributeError(
                    f"Target of {edge_class.__name__} must be ElectronicFrequencyConverter."
                )

    def add_node(self, obj: DexpiBaseModel) -> None:
        """Adds an object obj to the plant graph. The ID of the object is set as
        the node label. The object's class is set as the "dexpi_class"
        attribute.

        Parameters
        ----------
        obj : DexpiBaseModel
            DEXPI object to be added to the plant graph.
        """
        attributes = get_data_attributes(obj)
        attributes["dexpi_class"] = obj.__class__.__name__
        self.plant_graph.add_node(obj.id, **attributes)

    def add_edge(
        self,
        source: DexpiBaseModel,
        target: DexpiBaseModel,
        edge: DexpiBaseModel | tuple,
    ):
        """Adds an edge to the plant graph. If the source and target nodes are
        not in the graph yet, create them first. For PipingConnection, add the
        attributes from the PipingNetworkSegmentItem.

        Parameters
        ----------
        source : DexpiBaseModel
            Source node of the edge.
        target : DexpiBaseModel
            Target node of the edge.
        edge : DexpiBaseModel | tuple
            Edge type as a DEXPI class. For PipingConnection, provide a tuple
            with (PipingConnection, PipingNetworkSegmentItem).
        """
        if isinstance(edge, tuple):
            # attributes of pipingNetworkSegment
            attributes = get_data_attributes(edge[1])
            attributes["dexpi_class"] = edge[0].__class__.__name__
        else:
            attributes = get_data_attributes(edge)
            attributes["dexpi_class"] = edge.__class__.__name__

        try:
            self.validate_edge(
                source.__class__.__name__,
                target.__class__.__name__,
                attributes,
                special_edge_attributes=["dexpi_class"],
            )
        except Exception as e:
            warnings.warn(f"Edge cannot be established: {e}")
            return

        self.plant_graph.add_edge(source.id, target.id, **attributes)

    def parse_equipment_and_piping(self):
        """Create networkX graph from equipment and piping"""

        # create dictionary for nozzles of tagged plant items
        nozzles = {}

        # create TaggedPlantItem nodes
        tagged_plant_items = self.plant_model.conceptualModel.taggedPlantItems
        for tagged_plant_item in tagged_plant_items:
            if issubclass(tagged_plant_item.__class__, equipment.NozzleOwner):
                if tagged_plant_item.nozzles:
                    self.add_node(tagged_plant_item)
                    for nozzle in tagged_plant_item.nozzles:
                        nozzles[nozzle] = tagged_plant_item

        # create PipingNetworkSegmentItem nodes
        piping_network_systems = self.plant_model.conceptualModel.pipingNetworkSystems
        for piping_network_system in piping_network_systems:
            piping_network_segments = piping_network_system.segments
            for piping_network_segment in piping_network_segments:
                for item in piping_network_segment.items:
                    self.add_node(item)
                for connection in piping_network_segment.connections:
                    source_item = connection.sourceItem
                    target_item = connection.targetItem
                    if source_item and target_item:
                        if isinstance(source_item, equipment.Nozzle):
                            source_item = nozzles[source_item]
                        if isinstance(target_item, equipment.Nozzle):
                            target_item = nozzles[target_item]
                        self.add_edge(
                            source_item,
                            target_item,
                            (connection, piping_network_segment),
                        )

    def parse_instrumentation(self):
        """Extend graph of equipment and piping with instrumentation."""

        # create and link ControlledActuator nodes
        for actuating_system in self.plant_model.conceptualModel.actuatingSystems:
            valve_reference = actuating_system.operatedValveReference
            valve = valve_reference.valve
            actuator = actuating_system.controlledActuator
            if actuator:
                self.add_node(actuator)
                self.add_edge(actuator, valve, valve_reference)
            positioner = actuating_system.positioner
            if positioner:
                self.add_node(positioner)
                self.add_edge(positioner, valve, valve_reference)

        # create ProcessInstrumentationFunction nodes
        for instrumentation_fn in self.plant_model.conceptualModel.processInstrumentationFunctions:
            self.add_node(instrumentation_fn)
            # create ElectronicFrequencyConverter nodes
            for actuating_e_fn in instrumentation_fn.actuatingElectricalFunctions:
                for actuating_e_s in actuating_e_fn.systems:
                    for e_frequency_converter in actuating_e_s.electronicFrequencyConverter:
                        self.add_node(e_frequency_converter)
                        self.add_edge(
                            instrumentation_fn,
                            e_frequency_converter,
                            instrumentation.ElectronicFrequencyConverter(),
                        )
            # create SignalOffPageConnector nodes
            for signal_opc in instrumentation_fn.signalConnectors:
                self.add_node(signal_opc)
            # create SignalConveyingFunction edges
            for signal_conveying_function in instrumentation_fn.signalConveyingFunctions:
                target = self.determine_reference(signal_conveying_function.target)
                source = self.determine_reference(signal_conveying_function.source)
                self.add_edge(source, target, signal_conveying_function)
            # create nodes for OfflinePrimaryElement
            for process_signal_gen_fn in instrumentation_fn.processSignalGeneratingFunctions:
                if process_signal_gen_fn.systems is not None:
                    for system in process_signal_gen_fn.systems:
                        for primary_element in system.primaryElement:
                            if primary_element.__class__ == instrumentation.OfflinePrimaryElement:
                                self.add_edge(
                                    primary_element,
                                    instrumentation_fn,
                                    instrumentation.SignalLineFunction(),
                                )

    def determine_reference(self, dexpi_object: DexpiBaseModel) -> DexpiBaseModel:
        """Determine the references (Proteus: "association") of an object.
        - SignalConveyingFunction: source and target

        Parameters
        ----------
        dexpi_object : DexpiBaseModel
            DEXPI object that describes reference.

        Returns
        -------
        DexpiBaseModel
            List of DEXPI object to be used as reference.
        """
        if dexpi_object.__class__ == instrumentation.ProcessSignalGeneratingFunction:
            if dexpi_object.sensingLocation.__class__ == equipment.Nozzle:
                for tagged_plant_item in self.plant_model.conceptualModel.taggedPlantItems:
                    for nozzle in tagged_plant_item.nozzles:
                        if nozzle == dexpi_object.sensingLocation:
                            return tagged_plant_item
            elif issubclass(dexpi_object.sensingLocation.__class__, piping.PipingComponent):
                return dexpi_object.sensingLocation
            elif dexpi_object.sensingLocation.__class__ == piping.PipingNetworkSegment:
                raise NotImplementedError(
                    "Select a PipingComponent as the SensingLocation instead of the complete PipingNetworkSystem."
                )
        elif dexpi_object.__class__ == instrumentation.ActuatingFunction:
            return dexpi_object.systems.controlledActuator
        # ProcessInstrumentationFunction, SignalOffPageConnector
        else:
            return dexpi_object

    def draw_process_matplotlib(self) -> Figure:
        """Draw the process graph using matplotlib.pyplot.

        Returns
        -------
        go.Figure
            Figure object for Plotly.
        """
        draw_info = {"node_labels": {}, "node_colors": [], "edge_labels": {}}
        for node in self.plant_graph.nodes:
            class_name = self.plant_graph.nodes[node]["dexpi_class"]
            draw_info["node_labels"][node] = class_name
            if class_name in dir(piping):
                draw_info["node_colors"].append("red")
            elif class_name in dir(instrumentation):
                draw_info["node_colors"].append("blue")
            elif class_name in dir(equipment):
                draw_info["node_colors"].append("green")
        for edge in self.plant_graph.edges:
            draw_info["edge_labels"][edge] = self.plant_graph.edges[edge]["dexpi_class"]
        self.plant_graph = _add_positions(self.plant_graph, len(self.plant_graph.nodes))
        pos = nx.get_node_attributes(self.plant_graph, "pos")
        fig = plt.figure()
        nx.draw(
            self.plant_graph,
            pos,
            labels=draw_info["node_labels"],
            node_color=draw_info["node_colors"],
        )
        nx.draw_networkx_edge_labels(self.plant_graph, pos, edge_labels=draw_info["edge_labels"])
        return fig

    def draw_process_plotly(self) -> go.Figure:
        """Draw the process graph using Plotly.

        Returns
        -------
        go.Figure
            Figure object for Plotly.
        """
        # Initialize the draw info dictionary
        draw_info = {"node_labels": {}, "node_colors": [], "edge_labels": {}}

        # Extract node labels and colors
        for node in self.plant_graph.nodes:
            class_name = self.plant_graph.nodes[node]["dexpi_class"]
            draw_info["node_labels"][node] = class_name
            if class_name in dir(piping):
                draw_info["node_colors"].append("red")
            elif class_name in dir(instrumentation):
                draw_info["node_colors"].append("blue")
            elif class_name in dir(equipment):
                draw_info["node_colors"].append("green")
            else:
                draw_info["node_colors"].append("black")

        # Extract edge labels
        for edge in self.plant_graph.edges:
            draw_info["edge_labels"][edge] = self.plant_graph.edges[edge]["dexpi_class"]

        # Add positions for nodes
        self.plant_graph = _add_positions(
            self.plant_graph, len(self.plant_graph.nodes)
        )  # Or use nx.spring_layout
        pos = nx.get_node_attributes(self.plant_graph, "pos")

        # Create edge traces
        edge_x, edge_y = [], []
        for edge in self.plant_graph.edges:
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])  # None creates a break in the line
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y, line=dict(width=1, color="black"), hoverinfo="none", mode="lines"
        )

        # Create node traces
        node_x, node_y, node_color, node_text = [], [], [], []
        for node in self.plant_graph.nodes:
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_color.append(draw_info["node_colors"][list(self.plant_graph.nodes).index(node)])
            node_text.append(draw_info["node_labels"][node])

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_text,
            textposition="top center",
            marker=dict(size=10, color=node_color, line=dict(width=2)),
        )

        # Create edge label traces
        edge_label_x, edge_label_y, edge_label_text = [], [], []
        for edge, label in draw_info["edge_labels"].items():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_label_x.append((x0 + x1) / 2)  # Midpoint for edge label
            edge_label_y.append((y0 + y1) / 2)
            edge_label_text.append(label)

        edge_label_trace = go.Scatter(
            x=edge_label_x,
            y=edge_label_y,
            mode="text",
            text=edge_label_text,
            textfont=dict(color="black", size=10),
            hoverinfo="none",
        )

        # Combine traces into a Plotly figure
        fig = go.Figure(data=[edge_trace, node_trace, edge_label_trace])

        # Set layout for the figure
        fig.update_layout(
            showlegend=False,
            margin=dict(t=0, l=0, b=0, r=0),
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False),
        )

        return fig
