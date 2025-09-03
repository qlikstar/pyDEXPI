import networkx as nx
import pytest

from pydexpi.loaders import MLGraphLoader


@pytest.fixture
def graph_loader(loaded_example_dexpi):
    dexpi_model = loaded_example_dexpi
    my_graph_loader = MLGraphLoader()
    my_graph_loader.dexpi_to_graph(dexpi_model)
    return my_graph_loader


# @pytest.mark.dependency(depends=["loaded_example_graph"])
def test_graph_stats(graph_loader):
    """Test number of nodes and edges."""
    # Number of edges
    loaded_example_graph = graph_loader.plant_graph
    assert loaded_example_graph.number_of_edges() == 36

    # Number of nodes
    assert loaded_example_graph.number_of_nodes() == 33


# @pytest.mark.dependency(depends=["loaded_example_graph"])
def test_graph_integrity(graph_loader):
    """Test if the graph is completely connected."""
    loaded_example_graph = graph_loader.plant_graph
    # Number of independent subgraphs
    UG = nx.to_undirected(loaded_example_graph)
    sub_graphs = [UG.subgraph(c).copy() for c in nx.connected_components(UG)]
    assert len(sub_graphs) == 1


# @pytest.mark.dependency(depends=["loaded_example_graph"])
def test_graph_format(graph_loader):
    """Test the graph format using internal validation."""
    graph_loader.validate_graph_format()
