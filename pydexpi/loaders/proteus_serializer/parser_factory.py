"""Contains the factory for instantiating parser objects for XML elements."""

from collections.abc import Callable
from xml.etree import ElementTree as ET

from pydexpi.loaders.proteus_serializer.core import ModuleContext, ParserModule
from pydexpi.loaders.proteus_serializer.parser_modules import (
    ActuatingElectricalFunctionParser,
    ActuatingFunctionParser,
    ActuatingSystemComponentParser,
    ActuatingSystemParser,
    AssociationParser,
    CenterLineParser,
    ConnectionPointParser,
    EquipmentParser,
    GenericAttributeParser,
    InformationFlowParser,
    InstrumentationLoopFunctionParser,
    NozzleParser,
    OffPageConnectorReferenceParser,
    PipeOffPageConnectorParser,
    PipingComponentParser,
    PipingNetworkSegmentParser,
    PipingNetworkSystemParser,
    PipingNodeParser,
    PlantModelParser,
    ProcessInstrumentationFunctionParser,
    ProcessSignalGeneratingFunctionParser,
    ProcessSignalGeneratingSystemComponentParser,
    ProcessSignalGeneratingSystemParser,
    PropertyBreakParser,
    SignalOffPageConnectorParser,
)


class ParserFactory:
    """Factory class that creates parsers given an XML element.

    Includes a factory method for each xml element type and corresponding parser class. If not
    otherwise specified, the parser is created with the XML element and context as parameters, and
    returns an instance of the corresponding parser class. The top level method is
    `make_plant_model_parser`, which creates a parser for the top level plant model element.
    """

    def __init__(self) -> None:
        """Initialize the ParserFactory by creating the factory method registry for the instance."""
        self.factory_methods: dict[str, Callable[[ModuleContext, ET.Element], ParserModule]] = {
            "PlantModel": self.make_plant_model_parser,
            "ActuatingElectricalFunction": self.make_actuating_electrical_function_parser,
            "ActuatingFunction": self.make_actuating_function_parser,
            "ActuatingSystemComponent": self.make_actuating_system_component_parser,
            "ActuatingSystem": self.make_actuating_system_parser,
            "Association": self.make_association_parser,
            "CenterLine": self.make_center_line_parser,
            "ConnectionPoints": self.make_connection_point_parser,
            "Equipment": self.make_equipment_parser,
            "GenericAttribute": self.make_generic_attribute_parser,
            "InformationFlow": self.make_information_flow_parser,
            "InformationFlowOffPageConnectorReference": self.make_opc_reference_parser,
            "InstrumentationLoopFunction": self.make_instrumentation_loop_function_parser,
            "Nozzle": self.make_nozzle_parser,
            "PipeOffPageConnector": self.make_pipe_off_page_connector_parser,
            "PipeOffPageConnectorReference": self.make_opc_reference_parser,
            "PipingComponent": self.make_piping_component_parser,
            "PipingNetworkSegment": self.make_piping_network_segment_parser,
            "PipingNetworkSystem": self.make_piping_network_system_parser,
            "PipingNode": self.make_piping_node_parser,
            "ProcessInstrumentationFunction": self.make_process_instrumentation_function_parser,
            "ProcessSignalGeneratingFunction": (
                self.make_process_signal_generating_function_parser
            ),
            "ProcessSignalGeneratingSystemComponent": (
                self.make_process_signal_generating_system_component_parser
            ),
            "ProcessSignalGeneratingSystem": (self.make_process_signal_generating_system_parser),
            "PropertyBreak": self.make_property_break_parser,
            "InformationFlowOffPageConnector": self.make_signal_off_page_connector_parser,
        }

    def _parse_child_elements(
        self,
        parent_element: ET.Element,
        context: ModuleContext,
        element_tag: str,
        factory_method_key: str = None,
    ) -> list[ParserModule]:
        """Helper method to parse child elements of a given tag using the provided factory method.

        Parameters
        ----------
        parent_element : ET.Element
            The parent XML element containing child elements to parse.
        context : ModuleContext
            The context in which the XML element is being parsed.
        element_tag : str
            The tag name of the child elements to parse.
        factory_method_key : str
            The key corresponding to the factory method to use for creating parsers. If None, the
            element tag is used as the key.

        Returns
        -------
        list
            A list of parser instances created for the child elements.
        """
        if factory_method_key is None:
            factory_method_key = element_tag

        parsers = []
        for child in parent_element.findall(element_tag):
            sub_context = context.get_updated_context(child)
            parser = self.factory_methods[factory_method_key](sub_context, child)
            parsers.append(parser)
        return parsers

    def _create_parser_with_common_elements(
        self,
        parser_class: type,
        context: ModuleContext,
        element: ET.Element,
        parse_associations: bool = True,
        parse_generic_attributes: bool = True,
        **additional_parsers,
    ) -> ParserModule:
        """Helper to create parsers with common elements.

        Common elements include associations and generic attributes."""
        kwargs = {
            "context": context,
            "element": element,
        }

        if parse_associations:
            kwargs["association_parsers"] = self._parse_child_elements(
                element, context, "Association"
            )

        if parse_generic_attributes:
            kwargs["generic_attribute_parser"] = self.make_generic_attribute_parser(
                context, element
            )

        kwargs.update(additional_parsers)
        return parser_class(**kwargs)

    ### GENERIC MODULES ###
    def make_generic_attribute_parser(
        self, context: ModuleContext, parent_element: ET.Element
    ) -> GenericAttributeParser:
        """Creates a generic attribute parser for the given XML element.

        Note that the element is not the generic attribute element itself, but the parent
        element that contains the generic attributes.
        """
        return GenericAttributeParser(parent_element=parent_element, context=context)

    def make_association_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> AssociationParser:
        """Creates an association parser for the given XML element."""
        return AssociationParser(element=element, context=context)

    def make_opc_reference_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> OffPageConnectorReferenceParser:
        """Creates an off-page connector parser for the given XML element.

        Includes parsing associations and generic attributes.
        """
        opc_reference_parser = self._create_parser_with_common_elements(
            OffPageConnectorReferenceParser, context, element
        )

        return opc_reference_parser

    ### EQUIPMENT MODULES ###
    def make_nozzle_parser(self, context: ModuleContext, element: ET.Element) -> NozzleParser:
        """
        Creates a nozzle parser for the given XML element.

        Includes parsing connection points, associations, and generic attributes.
        """
        # Collect all connection point parsers defined in the nozzle
        connection_point_parsers = self._parse_child_elements(element, context, "ConnectionPoints")

        # Create and return the NozzleParser instance
        nozzle_parser = self._create_parser_with_common_elements(
            NozzleParser,
            context,
            element,
            connection_point_parsers=connection_point_parsers,
        )
        return nozzle_parser

    def make_equipment_parser(self, context: ModuleContext, element: ET.Element) -> EquipmentParser:
        """Creates an equipment parser for the given XML element.

        Includes parsing subequipment, nozzles, associations, and generic attributes.
        """
        # Make subequipment parsers
        subequipment_parsers = self._parse_child_elements(element, context, "Equipment")

        # Make nozzle parsers
        nozzle_parsers = self._parse_child_elements(element, context, "Nozzle")

        # Create and return the EquipmentParser instance
        equipment_parser = self._create_parser_with_common_elements(
            EquipmentParser,
            context,
            element,
            subequipment_parsers=subequipment_parsers,
            nozzle_parsers=nozzle_parsers,
        )
        return equipment_parser

    ### PIPING MODULES ###
    def make_piping_node_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> PipingNodeParser:
        """Creates a piping node parser for the given XML element with generic attributes."""

        # Create and return the PipingNodeParser instance
        node_parser = self._create_parser_with_common_elements(
            PipingNodeParser,
            context,
            element,
            parse_associations=False,
        )
        return node_parser

    def make_connection_point_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ConnectionPointParser:
        """Creates a connection point parser for the given XML element.

        Includes parsing piping nodes, which are nodes of type "process".
        """
        # Collect all piping node parsers defined in the connection point
        # These are nodes of type "process"
        piping_node_parsers = []
        for node in element.findall("Node"):
            if node.get("Type") == "process":
                sub_context = context.get_updated_context(node)
                piping_node_parsers.append(self.make_piping_node_parser(sub_context, node))

        # Create and return the ConnectionPointParser instance
        connection_point_parser = ConnectionPointParser(
            context=context,
            element=element,
            piping_node_parsers=piping_node_parsers,
        )
        return connection_point_parser

    def make_piping_component_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> PipingComponentParser:
        """Creates a piping component parser for the given XML element.

        Includes parsing connection points, associations, and generic attributes.
        """
        # Collect all connection point parsers defined in the piping component
        connection_point_parsers = self._parse_child_elements(element, context, "ConnectionPoints")

        parser = self._create_parser_with_common_elements(
            PipingComponentParser,
            context,
            element,
            connection_point_parsers=connection_point_parsers,
        )
        return parser

    def make_pipe_off_page_connector_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> PipeOffPageConnectorParser:
        """Creates an off-page connector parser for the given XML element.

        Includes parsing connection points, associations, and generic attributes.
        """
        # Collect all connection point parsers defined in the off-page connector
        connection_point_parsers = self._parse_child_elements(element, context, "ConnectionPoints")

        # Make reference parsers
        reference_parsers = self._parse_child_elements(
            element, context, "PipeOffPageConnectorReference"
        )

        parser = self._create_parser_with_common_elements(
            PipeOffPageConnectorParser,
            context,
            element,
            connection_point_parsers=connection_point_parsers,
            reference_parsers=reference_parsers,
        )

        return parser

    def make_property_break_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> PropertyBreakParser:
        """Creates a property break parser for the given XML element.

        Includes parsing connection points, associations, and generic attributes."""
        # Collect all connection point parsers defined in the property break
        connection_point_parsers = self._parse_child_elements(element, context, "ConnectionPoints")

        parser = self._create_parser_with_common_elements(
            PropertyBreakParser,
            context,
            element,
            connection_point_parsers=connection_point_parsers,
        )

        return parser

    def make_center_line_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> CenterLineParser:
        """Creates a center line parser for the given XML element with generic attributes."""
        return self._create_parser_with_common_elements(
            CenterLineParser,
            context,
            element,
            parse_associations=False,
        )

    def make_piping_network_segment_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> PipingNetworkSegmentParser:
        """
        Creates a piping network segment parser for the given XML element.

        Makes parsers for components, OPCs, property breaks, and center lines. Keep track of
        component, OPC, and property break parsers as items and center line parsers as
        connections. Also keep track of all parsers in order, as this is important to infer
        connectivity.
        """

        # Make parsers for components, OPCs, property breaks, and center lines. Keep track of
        # component, OPC, and property break parsers as items and center line parsers as
        # connections. Also keep track of all parsers in order, as this is important to infer
        # connectivity.
        ordered_element_parsers = []
        item_parsers = []
        center_line_parsers = []
        for subelement in element:
            if subelement.tag == "PipingComponent":
                sub_context = context.get_updated_context(subelement)
                component_parser = self.make_piping_component_parser(sub_context, subelement)
                ordered_element_parsers.append(component_parser)
                item_parsers.append(component_parser)
            elif subelement.tag == "PipeOffPageConnector":
                sub_context = context.get_updated_context(subelement)
                component_parser = self.make_pipe_off_page_connector_parser(sub_context, subelement)
                ordered_element_parsers.append(component_parser)
                item_parsers.append(component_parser)
            elif subelement.tag == "PropertyBreak":
                sub_context = context.get_updated_context(subelement)
                component_parser = self.make_property_break_parser(sub_context, subelement)
                ordered_element_parsers.append(component_parser)
                item_parsers.append(component_parser)
            elif subelement.tag == "CenterLine":
                sub_context = context.get_updated_context(subelement)
                component_parser = self.make_center_line_parser(sub_context, subelement)
                ordered_element_parsers.append(component_parser)
                center_line_parsers.append(component_parser)

        parser = self._create_parser_with_common_elements(
            PipingNetworkSegmentParser,
            context,
            element,
            ordered_element_parsers=ordered_element_parsers,
            item_parsers=item_parsers,
            center_line_parsers=center_line_parsers,
        )

        return parser

    def make_piping_network_system_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> PipingNetworkSystemParser:
        """Creates a piping network system parser for the given XML element.

        Includes parsing segments and generic attributes.
        """
        # Make segment parsers
        segment_parsers = self._parse_child_elements(element, context, "PipingNetworkSegment")

        # Create and return the PipingNetworkSystemParser instance
        parser = self._create_parser_with_common_elements(
            PipingNetworkSystemParser,
            context,
            element,
            segment_parsers=segment_parsers,
            parse_associations=False,
        )

        return parser

    ### Instrumentation modules ###
    def make_actuating_system_component_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ActuatingSystemComponentParser:
        """Creates an actuating system component parser for the given XML element.

        Includes parsing associations and generic attributes.
        """
        return self._create_parser_with_common_elements(
            ActuatingSystemComponentParser, context, element
        )

    def make_actuating_system_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ActuatingSystemParser:
        """Creates an actuating system parser for the given XML element.

        Includes parsing components and generic attributes.
        """
        # Make component parsers
        component_parsers = self._parse_child_elements(element, context, "ActuatingSystemComponent")

        # Create and return the ActuatingSystemParser instance
        parser = self._create_parser_with_common_elements(
            ActuatingSystemParser,
            context,
            element,
            component_parsers=component_parsers,
        )

        return parser

    def make_process_signal_generating_system_component_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ProcessSignalGeneratingSystemComponentParser:
        """Creates a process signal generating system component parser for the given XML element.

        Includes parsing associations and generic attributes.
        """
        return self._create_parser_with_common_elements(
            ProcessSignalGeneratingSystemComponentParser, context, element
        )

    def make_process_signal_generating_system_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ProcessSignalGeneratingSystemParser:
        """Creates a process signal generating system parser for the given XML element.

        Includes parsing components and generic attributes.
        """
        # Make component parsers
        component_parsers = self._parse_child_elements(
            element, context, "ProcessSignalGeneratingSystemComponent"
        )

        # Create and return the ProcessSignalGeneratingSystemParser instance
        parser = self._create_parser_with_common_elements(
            ProcessSignalGeneratingSystemParser,
            context,
            element,
            component_parsers=component_parsers,
            parse_associations=False,
        )

        return parser

    def make_actuating_function_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ActuatingFunctionParser:
        """Creates an actuating function parser for the given XML element.

        Includes parsing for generic attributes and associations.
        """
        return self._create_parser_with_common_elements(ActuatingFunctionParser, context, element)

    def make_actuating_electrical_function_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ActuatingElectricalFunctionParser:
        """Creates an actuating electrical function parser for the given XML element.

        Includes parsing for generic attributes and associations.
        """
        return self._create_parser_with_common_elements(
            ActuatingElectricalFunctionParser, context, element
        )

    def make_process_signal_generating_function_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ProcessSignalGeneratingFunctionParser:
        """Creates a process signal generating function parser for the given XML element.

        Includes parsing for generic attributes and associations.
        """
        return self._create_parser_with_common_elements(
            ProcessSignalGeneratingFunctionParser, context, element
        )

    def make_signal_off_page_connector_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> SignalOffPageConnectorParser:
        """Creates a signal off-page connector parser for the given XML element.

        Includes parsing references and associations.
        """
        # Make reference parsers
        reference_parsers = self._parse_child_elements(
            element, context, "InformationFlowOffPageConnectorReference"
        )

        parser = self._create_parser_with_common_elements(
            SignalOffPageConnectorParser,
            context,
            element,
            reference_parsers=reference_parsers,
            parse_generic_attributes=False,
        )

        return parser

    def make_information_flow_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> InformationFlowParser:
        """Creates an information flow parser for the given XML element.

        Includes parsing for generic attributes and associations.
        """
        return self._create_parser_with_common_elements(InformationFlowParser, context, element)

    def make_process_instrumentation_function_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> ProcessInstrumentationFunctionParser:
        """Creates a process instrumentation function parser for the given XML element.

        Includes parsing for actuating electrical functions, actuating functions, signal generating
        functions, signal opcs, signal conveying functions, generic attributes, and associations.
        """
        # Make actuating electrical function parsers
        actuating_electrical_function_parsers = self._parse_child_elements(
            element, context, "ActuatingElectricalFunction"
        )

        # Make actuating function parsers
        actuating_function_parsers = self._parse_child_elements(
            element, context, "ActuatingFunction"
        )

        # Make process signal generating function parsers
        process_signal_generating_function_parsers = self._parse_child_elements(
            element, context, "ProcessSignalGeneratingFunction"
        )

        # Make signal off-page connector parsers
        signal_off_page_connector_parsers = self._parse_child_elements(
            element, context, "InformationFlowOffPageConnector"
        )

        # Make information flow parsers
        information_flow_parsers = self._parse_child_elements(element, context, "InformationFlow")

        parser = self._create_parser_with_common_elements(
            ProcessInstrumentationFunctionParser,
            context,
            element,
            actuating_electrical_function_parsers=actuating_electrical_function_parsers,
            actuating_function_parsers=actuating_function_parsers,
            signal_generating_function_parsers=process_signal_generating_function_parsers,
            signal_opc_parsers=signal_off_page_connector_parsers,
            information_flow_parsers=information_flow_parsers,
        )

        # Create and return the ProcessInstrumentationFunctionParser instance
        return parser

    def make_instrumentation_loop_function_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> InstrumentationLoopFunctionParser:
        """Creates an instrumentation loop function parser for the given XML element.

        Includes parsing associations and generic attributes.
        """
        return self._create_parser_with_common_elements(
            InstrumentationLoopFunctionParser, context, element
        )

    ### MODEL PARSERS ###
    def make_plant_model_parser(
        self, context: ModuleContext, element: ET.Element
    ) -> PlantModelParser:
        """Creates a plant model parser for the given XML element.

        Includes parsing equipment, piping network systems, and actuating systems.
        """
        # Make equipment parsers
        equipment_parsers = self._parse_child_elements(element, context, "Equipment")

        # Make piping network system parsers
        piping_network_system_parsers = self._parse_child_elements(
            element, context, "PipingNetworkSystem"
        )

        # Make actuating system parsers
        actuating_system_parsers = self._parse_child_elements(element, context, "ActuatingSystem")

        # Make process signal generating system parsers
        process_signal_generating_system_parsers = self._parse_child_elements(
            element, context, "ProcessSignalGeneratingSystem"
        )

        # Make process instrumentation function parsers
        process_instrumentation_function_parsers = self._parse_child_elements(
            element, context, "ProcessInstrumentationFunction"
        )

        # Make instrumentation loop function parsers
        instrumentation_loop_function_parsers = self._parse_child_elements(
            element, context, "InstrumentationLoopFunction"
        )

        return PlantModelParser(
            context=context,
            element=element,
            equipment_parsers=equipment_parsers,
            piping_network_system_parsers=piping_network_system_parsers,
            actuating_system_parsers=actuating_system_parsers,
            process_signal_generating_system_parsers=process_signal_generating_system_parsers,
            process_instrumentation_function_parsers=process_instrumentation_function_parsers,
            instrumentation_loop_function_parsers=instrumentation_loop_function_parsers,
        )
