import sys
import networkx as nx
import plotly.graph_objects as go
import numpy as np
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from config import (EDGE_POINTS_QUANTITY, EDGE_POINTS_OPACITY)

# References:
# - https://stackoverflow.com/questions/74607000/python-networkx-plotly-how-to-display-edges-mouse-over-text
# - https://stackoverflow.com/questions/49234144/networkx-node-size-must-correlate-to-dimension
# - https://matplotlib.org/stable/users/explain/colors/colormaps.html


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


def create_plotly_graph(G, pos, edge_weights,
                        node_total_no_of_signers_combined_dict,
                        volume_threshold, earliest_local_block_time,
                        latest_local_block_time, is_filtered):
    edge_x_1 = []
    edge_y_1 = []
    edge_x_2 = []
    edge_y_2 = []

    edge_middle_x = []
    edge_middle_y = []
    edge_hover_text = []

    annotations = []

    min_weight = min(edge_weights)
    max_weight = max(edge_weights)

    total_no_of_signers_combined_list = [
        no_of_signers
        for _, no_of_signers in node_total_no_of_signers_combined_dict.items()
    ]
    min_no_of_signers_combined = min(total_no_of_signers_combined_list)
    max_no_of_signers_combined = max(total_no_of_signers_combined_list)

    node_x = []
    node_y = []
    node_sizes = []
    node_hover_text = []
    node_colours = []

    fdv_values = np.array([G.nodes[node]['fdv'] for node in G.nodes()])
    min_fdv, max_fdv = fdv_values.min(), fdv_values.max()
    norm_node_sizes = 200 + 1000 * (fdv_values - min_fdv) / (max_fdv - min_fdv)

    for node, size in zip(G.nodes(), norm_node_sizes):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

        node_sizes.append(size)

        node_total_no_of_signers_combined = node_total_no_of_signers_combined_dict.get(
            node, 0)

        node_info = '{} ({})<br>Mint Address: {}<br>FDV: {:,.2f} USD<br>Website: {}<br>Telegram: {}<br>Twitter: {}<br>Combined No. of Wallet Addresses that interacts with the Token: {}'.format(
            G.nodes[node]['name'], G.nodes[node]['symbol'],
            G.nodes[node]['mint_address'], G.nodes[node]['fdv'],
            G.nodes[node]['website'], G.nodes[node]['telegram'],
            G.nodes[node]['twitter'], node_total_no_of_signers_combined)

        node_hover_text.append(node_info)

        node_colour = weight_to_color(node_total_no_of_signers_combined,
                                      min_no_of_signers_combined,
                                      max_no_of_signers_combined,
                                      cmap=plt.cm.plasma,
                                      use_log=False)
        node_colours.append(node_colour)

    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        midpoint_x = (x0 + x1) / 2
        midpoint_y = (y0 + y1) / 2
        edge_x_1.extend([x0, midpoint_x, None])
        edge_y_1.extend([y0, midpoint_y, None])
        edge_x_2.extend([midpoint_x, x1, None])
        edge_y_2.extend([midpoint_y, y1, None])

        middle_x, middle_y = make_middle_points(x0, x1, y0, y1,
                                                EDGE_POINTS_QUANTITY)
        edge_middle_x.extend(middle_x)
        edge_middle_y.extend(middle_y)

        edge_info = '{} --> {}<br>Net Volume: {:,.2f} USD<br>Volume from {} --> {}: {:,.2f} USD<br>Volume from {} --> {}: {:,.2f} USD<br>No. of Unique Wallet Addresses Combined: {}<br>No. of Unique Wallet Addresses that swaps from {} --> {}: {}<br>No. of Unique Wallet Addresses that swaps from {} --> {}: {}'.format(
            G.nodes[edge[0]]['name'] + ' (' + G.nodes[edge[0]]['symbol'] + ')',
            G.nodes[edge[1]]['name'] + ' (' + G.nodes[edge[1]]['symbol'] + ')',
            G.edges[edge]['weight_net'], G.nodes[edge[0]]['symbol'],
            G.nodes[edge[1]]['symbol'], G.edges[edge]['weight_forward'],
            G.nodes[edge[1]]['symbol'], G.nodes[edge[0]]['symbol'],
            G.edges[edge]['weight_reverse'],
            G.edges[edge]['no_of_signers_combined'],
            G.nodes[edge[0]]['symbol'], G.nodes[edge[1]]['symbol'],
            G.edges[edge]['no_of_signers_forward'], G.nodes[edge[1]]['symbol'],
            G.nodes[edge[0]]['symbol'], G.edges[edge]['no_of_signers_reverse'])

        edge_hover_text.extend([edge_info] * EDGE_POINTS_QUANTITY)

        arrow_color = weight_to_color(G.edges[edge]['weight_net'], min_weight,
                                      max_weight)

        annotations.append(
            dict(ax=x0,
                 ay=y0,
                 x=midpoint_x,
                 y=midpoint_y,
                 xref='x',
                 yref='y',
                 axref='x',
                 ayref='y',
                 showarrow=True,
                 arrowhead=4,
                 arrowsize=2,
                 arrowwidth=2,
                 arrowcolor=arrow_color))

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
                 arrowhead=0,
                 arrowsize=2,
                 arrowwidth=2,
                 arrowcolor=arrow_color))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=[
            G.nodes[node]['name'] + ' (' + G.nodes[node]['symbol'] + ')'
            for node in G.nodes()
        ],
        textposition="top center",
        hoverinfo='text',
        textfont=dict(size=10),
        hovertext=node_hover_text,
        hoverlabel=dict(bgcolor='mistyrose', font=dict(color='darkred')),
        marker=dict(
            color=node_colours,
            size=node_sizes,  # Node size based on normalized 'fdv'
            sizemode='area',
            line_width=2))

    edge_trace_1 = go.Scatter(x=edge_x_1,
                              y=edge_y_1,
                              line=dict(width=3, color='rgba(0,0,0,0)'),
                              hoverinfo='text',
                              mode='lines')

    edge_trace_2 = go.Scatter(x=edge_x_2,
                              y=edge_y_2,
                              line=dict(width=3, color='rgba(0,0,0,0)'),
                              hoverinfo='text',
                              mode='lines')

    mnode_trace = go.Scatter(x=edge_middle_x,
                             y=edge_middle_y,
                             mode="markers",
                             showlegend=False,
                             hovertemplate="%{hovertext}<extra></extra>",
                             hovertext=edge_hover_text,
                             hoverlabel=dict(bgcolor='lightblue',
                                             font=dict(color='darkblue')),
                             marker=go.Marker(opacity=EDGE_POINTS_OPACITY))

    colorbar_trace_1 = go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(
            colorscale='Viridis',
            cmin=min_weight,
            cmax=max_weight,
            colorbar=dict(
                title='Edge Weight (Net Volume in USD)',
                titleside='right',
                thickness=15,
                tickvals=[min_weight, max_weight],
                ticktext=[f'{min_weight:.2f}', f'{max_weight:.2f}'],
                tickformat='.2f',
                tickmode='array',
                x=1,  # Adjust the colorbar position
                y=0.5,  # Centering the colorbar vertically
            )),
        showlegend=False,
        hoverinfo='none')

    colorbar_trace_2 = go.Scatter(
        x=[None],
        y=[None],
        mode='markers',
        marker=dict(
            colorscale='Plasma',
            cmin=min_no_of_signers_combined,
            cmax=max_no_of_signers_combined,
            colorbar=dict(
                title=
                'Combined No. of Wallet Addresses (Unique per Edge) that interacts with the Token',
                titleside='right',
                thickness=15,
                tickvals=[
                    min_no_of_signers_combined, max_no_of_signers_combined
                ],
                ticktext=[
                    f'{min_no_of_signers_combined}',
                    f'{max_no_of_signers_combined}'
                ],
                tickformat='d',
                tickmode='array',
                x=1.05,  # Position to the right of the first colorbar
                y=0.5,  # Centering the colorbar vertically
                len=0.75)),
        showlegend=False,
        hoverinfo='none')

    fig = go.Figure(
        data=[
            edge_trace_1, edge_trace_2, node_trace, mnode_trace,
            colorbar_trace_1, colorbar_trace_2
        ],
        layout=go.Layout(
            title=dict(
                text=
                ('<span style="font-size:24px;font-weight:bold;color:black;text-decoration:underline;">Underground DEX Trades</span><br>'
                 '<span style="font-size:16px;color:black;"><i>Transactions from {} to {}</i></span><br>'
                 '<span style="font-size:16px;color:black;"><i>Minimum Volume Threshold: {:,.2f} USD</i></span><br>'
                 '<span style="font-size:16px;color:black;"><i>Filtered: {}</i></span><br>'
                 ).format(earliest_local_block_time, latest_local_block_time,
                          volume_threshold, is_filtered),
                font=dict(size=20,
                          color='black',
                          family='Arial',
                          weight='bold'),  # Set the font weight to bold
                y=0.95,  # Adjust this value to shift the title upwards
                x=0.03  # Adjust this value to shift the title upwards
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=10, l=5, r=5, t=10),
            annotations=annotations,
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)))

    return fig


def plot_nodes_edges_graph(graph_data, plot_filtered_addresses,
                           volume_threshold, is_filtered):

    G = nx.DiGraph()

    nodes = graph_data.get('nodes', {})
    edges = graph_data.get('edges', {})
    transaction_window = graph_data.get('transaction_window', {})
    earliest_local_block_time = transaction_window.get(
        'earliest_local_block_time', 'Not Recorded')
    latest_local_block_time = transaction_window.get('latest_local_block_time',
                                                     'Not Recorded')

    edge_weights = []
    filtered_nodes = set()
    node_total_no_of_signers_combined_dict = {}

    for edge, edge_detail in edges.items():
        source, target = edge.split('-')
        weight_forward = edge_detail['trade_amount_in_usd_forward']
        weight_reverse = edge_detail['trade_amount_in_usd_reverse']
        weight_net = edge_detail['trade_amount_in_usd_net']
        no_of_signers_forward = edge_detail['no_of_signers_forward']
        no_of_signers_reverse = edge_detail['no_of_signers_reverse']
        no_of_signers_combined = edge_detail['no_of_signers_combined']

        if plot_filtered_addresses:
            if source not in plot_filtered_addresses and target not in plot_filtered_addresses:
                continue

        if weight_net == 0:
            continue
        elif weight_net < 0:
            temp_source = target
            target = source
            source = temp_source

            temp_weight_reverse = weight_forward
            weight_forward = weight_reverse
            weight_reverse = temp_weight_reverse

            temp_no_of_signers_reverse = no_of_signers_forward
            no_of_signers_forward = no_of_signers_reverse
            no_of_signers_reverse = temp_no_of_signers_reverse

            weight_net = abs(weight_net)

        if weight_net < volume_threshold:
            continue

        if source not in node_total_no_of_signers_combined_dict:
            node_total_no_of_signers_combined_dict[
                source] = no_of_signers_combined
        else:
            node_total_no_of_signers_combined_dict[
                source] += no_of_signers_combined

        if target not in node_total_no_of_signers_combined_dict:
            node_total_no_of_signers_combined_dict[
                target] = no_of_signers_combined
        else:
            node_total_no_of_signers_combined_dict[
                target] += no_of_signers_combined

        filtered_nodes.add(source)
        filtered_nodes.add(target)
        edge_weights.append(weight_net)

        G.add_edge(source,
                   target,
                   weight_forward=weight_forward,
                   weight_reverse=weight_reverse,
                   weight_net=weight_net,
                   no_of_signers_forward=no_of_signers_forward,
                   no_of_signers_reverse=no_of_signers_reverse,
                   no_of_signers_combined=no_of_signers_combined)

    if not edge_weights:
        print('\nNo graph data available to plot.\n')
        sys.exit(1)

    for node, attributes in nodes.items():
        if node in filtered_nodes:
            G.add_node(node, **attributes)

    pos = nx.spiral_layout(G,
                           scale=1,
                           center=None,
                           dim=2,
                           resolution=0.8,
                           equidistant=True)

    fig = create_plotly_graph(G, pos, edge_weights,
                              node_total_no_of_signers_combined_dict,
                              volume_threshold, earliest_local_block_time,
                              latest_local_block_time, is_filtered)
    fig.show()
