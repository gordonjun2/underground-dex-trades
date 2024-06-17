import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import requests
from plot_graph import create_plotly_graph, G, pos

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Graph(id='graph', figure=create_plotly_graph(G, pos)),
    dcc.Graph(id='time-series')
])


@app.callback(Output('time-series', 'figure'), [Input('graph', 'clickData')])
def display_time_series(clickData):
    if clickData is None:
        return {}

    node_id = clickData['points'][0]['text'].split('<br>')[0]
    url = f'http://your_backend_api_endpoint/{node_id}'

    response = requests.get(url)
    data = response.json()

    fig = px.line(data,
                  x='time',
                  y=['series1', 'series2'],
                  title=f'Time Series for {node_id}')

    return fig


# if __name__ == '__main__':
#     app.run_server(debug=True)
