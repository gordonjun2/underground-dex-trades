graph = {
    'nodes': {
        'A': {
            'name': 'Node A',
            'value': 1
        },
        'B': {
            'name': 'Node B',
            'value': 2
        },
        'C': {
            'name': 'Node C',
            'value': 3
        },
        'D': {
            'name': 'Node D',
            'value': 4
        },
    },
    'edges': [{
        'source': 'A',
        'target': 'B',
        'weight': 5
    }, {
        'source': 'A',
        'target': 'C',
        'weight': 3
    }, {
        'source': 'B',
        'target': 'D',
        'weight': 4
    }, {
        'source': 'C',
        'target': 'D',
        'weight': 2
    }]
}

import networkx as nx
import matplotlib.pyplot as plt

# Create a graph object
G = nx.Graph()

# Add nodes
for node, attrs in graph['nodes'].items():
    G.add_node(node, **attrs)

# Add edges
for edge in graph['edges']:
    G.add_edge(edge['source'], edge['target'], weight=edge['weight'])

# Draw the graph
pos = nx.spring_layout(G)
nx.draw(G,
        pos,
        with_labels=True,
        node_size=700,
        node_color="skyblue",
        font_size=10,
        font_color="black")
labels = nx.get_edge_attributes(G, 'weight')
nx.draw_networkx_edge_labels(G, pos, edge_labels=labels)
plt.show()
