"""Example python file with a function."""

import json
import urllib.parse

import networkx as nx
import requests
from bs4 import BeautifulSoup
from typeguard import typechecked


def add_weighted_edge(*, graph, source, target):
    if graph.has_edge(source, target):
        graph[source][target]["weight"] += 1
    else:
        graph.add_edge(source, target, weight=1)


@typechecked
def website_to_graph(
    *,
    root_url: str,
    previous_url: str,
    new_url: str,
    website_graph: nx.DiGraph,
):
    """Crawls a website and its sub URLs, building a directed graph using
    NetworkX. Nodes represent URLs and edges point to child URLs. Each node has
    a 'text_content' attribute to store the extracted text.

    Args:
      url: The starting URL of the website.
    """
    try:
        response = requests.get(new_url)
        response.raise_for_status()  # Raise exception for non-2xx status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {new_url}: {e}")
        return website_graph

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract text content (replace with your preferred method if needed)
    text_content = soup.get_text(separator="\n").strip()

    # Create a graph and add the current URL as a node with text content
    # website_graph.add_node(new_url.replace(":", ""), text_content=text_content)
    website_graph.add_node(new_url, text_content=get_main_text(url=new_url))
    
    # Find all links on the page and recursively crawl them
    for link in soup.find_all("a", href=True):
        new_url: str = urllib.parse.urljoin(root_url, link["href"])
        
        # Check if link points to the same domain and is not an external link
        if link["href"].startswith("/") and link["href"] != "/":
            
            # First add the new node and text content, then add edge to new node.
            if new_url not in website_graph.nodes:
                website_to_graph(
                    root_url=root_url,
                    previous_url=new_url,
                    new_url=new_url,
                    website_graph=website_graph,
                )
            add_weighted_edge(
                graph=website_graph, source=previous_url, target=new_url
            )
    return website_graph


def get_main_text(*, url: str):
    # Fetch the content of the URL
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract main text (example: getting all the text inside <p> tags)
    main_text = ""
    for p_tag in soup.find_all("p"):
        main_text += p_tag.get_text() + "\n"
    return main_text


def graph_to_json(G: nx.DiGraph, filepath: str):
    """Exports a NetworkX graph (G) to a JSON file (filepath).

    Args:
        G: A NetworkX graph to be exported.
        filepath: Path to the output JSON file.
    """
    # Use nx.node_link_data to get nodes and edges in JSON format
    data = nx.node_link_data(G)
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)  # Add indentation for readability


def load_from_json(filepath):
    """Loads data from a JSON file.

    Args:
        filepath: Path to the JSON file.

    Returns:
        The loaded data as a Python object.
    """
    try:
        with open(filepath) as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON file - {filepath}")
        return None


def json_to_graph(filepath: str) -> nx.DiGraph:
    """Loads a directed graph from a JSON file generated by `graph_to_json`.

    Args:
        filepath: Path to the JSON file containing graph data.

    Returns:
        A NetworkX DiGraph representing the loaded graph.
    """
    # Read data from the JSON file
    with open(filepath) as f:
        data = json.load(f)

    # Create a directed graph
    G = nx.DiGraph()

    # Add nodes with attributes (if present)
    for node in data["nodes"]:
        page_main_text:str=node["text_content"]
        attributes = node.get(
            "attributes", {}
        )  # Handle potential missing attributes
        
        G.add_node(node["id"], text_content=page_main_text)  # Unpack attributes dictionary

    # Add edges
    for edge in data["links"]:
        G.add_edge(edge["source"], edge["target"])

    return G
