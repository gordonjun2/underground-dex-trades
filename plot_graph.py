import networkx as nx
import plotly.graph_objects as go
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import math

# References:
# - https://stackoverflow.com/questions/74607000/python-networkx-plotly-how-to-display-edges-mouse-over-text
# - https://stackoverflow.com/questions/49234144/networkx-node-size-must-correlate-to-dimension

EDGE_POINTS_QUANTITY = 50
EDGE_POINTS_OPACITY = 0


def queue(a, b, qty):
    """either x0 and x1 or y0 and y1, qty of points to create"""
    q = deque()
    q.append((0, qty - 1))  # indexing starts at 0
    pts = [0] * qty
    pts[0] = a
    pts[-1] = b  # x0 is the first value, x1 is the last
    while len(q) != 0:
        left, right = q.popleft()  # remove working segment from queue
        center = (left + right + 1) // 2  # creates index values for pts
        pts[center] = (pts[left] + pts[right]) / 2
        if right - left > 2:  # stop when qty met
            q.append((left, center))
            q.append((center, right))
    return pts


def make_middle_points(first_x, last_x, first_y, last_y, qty):
    """line segment end points, how many midpoints, hovertext"""
    # Add 2 because the origin will be in the list, pop first and last (the nodes)
    middle_x_ = queue(first_x, last_x, qty + 2)
    middle_y_ = queue(first_y, last_y, qty + 2)
    middle_x_.pop(0)
    middle_x_.pop()
    middle_y_.pop(0)
    middle_y_.pop()
    return middle_x_, middle_y_


def weight_to_color(weight,
                    min_weight,
                    max_weight,
                    cmap=plt.cm.viridis,
                    use_log=True):
    """Function to map weight to a color using a colormap."""

    if use_log:
        log_weight = np.log10(weight)
        norm = mcolors.Normalize(vmin=np.log10(min_weight),
                                 vmax=np.log10(max_weight))

        return mcolors.to_hex(cmap(norm(log_weight)))
    else:
        norm = mcolors.Normalize(vmin=min_weight, vmax=max_weight)

        return mcolors.to_hex(cmap(norm(weight)))


def create_plotly_graph(G, pos, edge_weights):
    edge_x = []
    edge_y = []

    edge_middle_x = []
    edge_middle_y = []
    edge_hover_text = []

    annotations = []

    min_weight = min(edge_weights)
    max_weight = max(edge_weights)

    node_x = []
    node_y = []
    node_size = []
    node_hover_text = []

    fdv_values = np.array([G.nodes[node]['fdv'] for node in G.nodes()])
    min_fdv, max_fdv = fdv_values.min(), fdv_values.max()
    norm_node_size = 200 + 1000 * (fdv_values - min_fdv) / (max_fdv - min_fdv)

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

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

        middle_x, middle_y = make_middle_points(x0, x1, y0, y1,
                                                EDGE_POINTS_QUANTITY)
        edge_middle_x.extend(middle_x)
        edge_middle_y.extend(middle_y)

        edge_info = '{} --> {}<br>Net Volume: {:.2f} USD'.format(
            G.nodes[edge[0]]['name'] + ' (' + G.nodes[edge[0]]['symbol'] + ')',
            G.nodes[edge[1]]['name'] + ' (' + G.nodes[edge[1]]['symbol'] + ')',
            G.edges[edge]['weight'])
        edge_hover_text.extend([edge_info] * EDGE_POINTS_QUANTITY)

        arrow_color = weight_to_color(G.edges[edge]['weight'], min_weight,
                                      max_weight)
        annotations.append(
            dict(ax=x0,
                 ay=y0,
                 x=x1,
                 y=y1,
                 xref='x',
                 yref='y',
                 axref='x',
                 ayref='y',
                 showarrow=True,
                 arrowhead=1,
                 arrowsize=2,
                 arrowwidth=2,
                 arrowcolor=arrow_color))

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
            size=node_size,  # Node size based on normalized 'fdv'
            sizemode='area',
            line_width=2))

    edge_trace = go.Scatter(x=edge_x,
                            y=edge_y,
                            line=dict(width=3),
                            hoverinfo='text',
                            mode='lines')

    mnode_trace = go.Scatter(x=edge_middle_x,
                             y=edge_middle_y,
                             mode="markers",
                             showlegend=False,
                             hovertemplate="%{hovertext}<extra></extra>",
                             hovertext=edge_hover_text,
                             marker=go.Marker(opacity=EDGE_POINTS_OPACITY))

    colorbar_trace = go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(colorscale='Viridis',
                    cmin=min_weight,
                    cmax=max_weight,
                    colorbar=dict(
                        title='Edge Weight (Net Volume in USD)',
                        titleside='right',
                        thickness=15,
                        tickvals=[min_weight, max_weight],
                        ticktext=[f'{min_weight:.2f}', f'{max_weight:.2f}'],
                        tickformat='.2f',
                        tickmode='array')),
        showlegend=False,
        hoverinfo='none')

    fig = go.Figure(
        data=[edge_trace, node_trace, mnode_trace, colorbar_trace],
        layout=go.Layout(
            title=dict(
                text='<br>Underground DEX Trades',
                font=dict(size=24,
                          color='black',
                          family='Arial',
                          weight='bold'),  # Set the font weight to bold
                y=1  # Adjust this value to shift the title upwards
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=annotations,
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)))

    return fig


def plot_nodes_edges_graph(graph_data, volume_threshold=0):

    G = nx.DiGraph()

    nodes = graph_data['nodes']
    edges = graph_data['edges']

    edge_weights = []

    for node, attributes in nodes.items():
        G.add_node(node, **attributes)

    for edge, weight in edges.items():
        source, target = edge.split('-')

        if weight == 0:
            continue
        elif weight < 0:
            temp_source = target
            target = source
            source = temp_source
            weight = abs(weight)

        if weight < volume_threshold:
            continue

        edge_weights.append(weight)

        G.add_edge(source, target, weight=weight)

    pos = nx.shell_layout(
        G,
        nlist=None,  # List of lists of nodes to place in each shell
        rotate=None,
        scale=1,
        center=(0, 0))

    fig = create_plotly_graph(G, pos, edge_weights)
    fig.show()
