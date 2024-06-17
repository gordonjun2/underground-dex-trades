import networkx as nx
import plotly.graph_objects as go


def create_plotly_graph(G, pos):
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(x=edge_x,
                            y=edge_y,
                            line=dict(width=0.5, color='#888'),
                            hoverinfo='none',
                            mode='lines')

    node_x = []
    node_y = []
    node_hover_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_info = '{} ({})<br>Mint Address: {}<br>FDV: {}<br>Website: {}<br>Telegram: {}<br>Twitter: {}'.format(
            G.nodes[node]['name'], G.nodes[node]['symbol'],
            G.nodes[node]['mint_address'], G.nodes[node]['fdv'],
            G.nodes[node]['website'], G.nodes[node]['telegram'],
            G.nodes[node]['twitter'])
        node_hover_text.append(node_info)

    node_trace = go.Scatter(x=node_x,
                            y=node_y,
                            mode='markers+text',
                            text=[G.nodes[node]['name'] for node in G.nodes()],
                            textposition="top center",
                            hoverinfo='text',
                            textfont=dict(size=10),
                            hovertext=node_hover_text,
                            marker=dict(showscale=True,
                                        colorscale='YlGnBu',
                                        size=10,
                                        colorbar=dict(thickness=15,
                                                      title='Node Connections',
                                                      xanchor='left',
                                                      titleside='right'),
                                        line_width=2))

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title='<br>Underground DEX Trades',
            titlefont_size=16,
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text=
                    "Python code: <a href='https://plotly.com/~jackp/17426/'> https://plotly.com/~jackp/17426/</a>",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002)
            ],
            xaxis=dict(showgrid=False, zeroline=False),
            yaxis=dict(showgrid=False, zeroline=False)))

    return fig


def plot_nodes_edges_graph(graph_data):

    G = nx.DiGraph()

    nodes = graph_data['nodes']
    edges = graph_data['edges']

    for node, attributes in nodes.items():
        G.add_node(node, **attributes)

    for (source, target), weight in edges.items():
        G.add_edge(source, target, weight=weight)

    pos = nx.spring_layout(G)

    fig = create_plotly_graph(G, pos)
    fig.show()
