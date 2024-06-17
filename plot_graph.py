import networkx as nx
import plotly.graph_objects as go
import numpy as np


def create_plotly_graph(G, pos):
    edge_x = []
    edge_y = []
    edge_hover_text = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
        edge_info = '{} -- {}<br>Volume: {}'.format(
            G.nodes[edge[0]]['name'] + '(' + G.nodes[edge[0]]['symbol'] + ')',
            G.nodes[edge[1]]['name'] + '(' + G.nodes[edge[1]]['symbol'] + ')',
            G.edges[edge]['weight'])
        edge_hover_text.append(edge_info)

    edge_trace = go.Scatter(x=edge_x,
                            y=edge_y,
                            line=dict(width=3, color='#888'),
                            hoverinfo='text',
                            mode='lines',
                            hovertext=edge_hover_text)

    node_x = []
    node_y = []
    node_size = []
    node_hover_text = []

    # Extract FDV values and normalize them
    fdv_values = np.array([G.nodes[node]['fdv'] for node in G.nodes()])
    min_fdv, max_fdv = fdv_values.min(), fdv_values.max()
    norm_node_size = 200 + 500 * (fdv_values - min_fdv) / (
        max_fdv - min_fdv)  # Normalized to a range of 10 to 50

    for node, size in zip(G.nodes(), norm_node_size):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_size.append(size)
        node_info = '{} ({})<br>Mint Address: {}<br>FDV: {}<br>Website: {}<br>Telegram: {}<br>Twitter: {}'.format(
            G.nodes[node]['name'], G.nodes[node]['symbol'],
            G.nodes[node]['mint_address'], G.nodes[node]['fdv'],
            G.nodes[node]['website'], G.nodes[node]['telegram'],
            G.nodes[node]['twitter'])
        node_hover_text.append(node_info)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=[G.nodes[node]['name'] for node in G.nodes()],
        textposition="top center",
        hoverinfo='text',
        textfont=dict(size=10),
        hovertext=node_hover_text,
        marker=dict(
            showscale=True,
            colorscale='YlGnBu',
            size=node_size,  # Node size based on normalized 'fdv'
            sizemode='area',
            colorbar=dict(thickness=15,
                          title='Node Connections',
                          xanchor='left',
                          titleside='right'),
            line_width=2))

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(title='<br>Underground DEX Trades',
                                     titlefont_size=16,
                                     showlegend=False,
                                     hovermode='closest',
                                     margin=dict(b=20, l=5, r=5, t=40),
                                     annotations=[],
                                     xaxis=dict(showgrid=False,
                                                zeroline=False),
                                     yaxis=dict(showgrid=False,
                                                zeroline=False)))

    return fig


def plot_nodes_edges_graph(graph_data):

    G = nx.DiGraph()

    nodes = graph_data['nodes']
    edges = graph_data['edges']

    for node, attributes in nodes.items():
        G.add_node(node, **attributes)

    for edge, weight in edges.items():
        source, target = edge.split('-')
        G.add_edge(source, target, weight=weight)

    pos = nx.spring_layout(G, seed=42)

    fig = create_plotly_graph(G, pos)
    fig.show()
