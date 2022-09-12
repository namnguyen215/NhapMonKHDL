import pandas as pd  # organize the data
import plotly.express as px
import dash
from dash import dash_table
from dash import dcc  # create interactive components
from dash import html  # access html tags
from dash.dependencies import Input, Output
import json
import requests

app = dash.Dash(__name__)  # start the app


url = "https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/ncov_cases2_v1/FeatureServer/2/query?where=1%3D1&outFields=Country_Region,Confirmed,Deaths,Mortality_Rate,ISO3&returnGeometry=false&outSR=4326&f=json"
rq = requests.get(url).text
data = json.loads(rq)
df = pd.json_normalize(data["features"])
df.rename(columns={'attributes.Country_Region': 'Quốc gia', 'attributes.Confirmed': 'Số ca',
          'attributes.Deaths': 'Tử vong', 'attributes.Mortality_Rate': 'Tỉ lệ tử vong', 'attributes.ISO3': 'id'}, inplace=True)
df['Tỉ lệ tử vong'] = df['Tỉ lệ tử vong'].map('{:,.2f}'.format)
df.set_index('id', inplace=True, drop=False)
dff = df.sort_values(by=['Số ca'], ascending=False)


def total():
    cases = dff['Số ca'].sum()
    deaths = dff['Tử vong'].sum()
    return cases, deaths


cases, deaths = total()



app.layout = html.Div([
    html.Div(id="map"),
    html.Div(id="total", children=[
        html.Div("Tổng số ca nhiễm: "+"{:,}".format(cases)),
        html.Div("Tổng số ca tử vong: "+"{:,}".format(deaths))
    ]),
    dash_table.DataTable(
        id='datatable-row-ids',
        columns=[
            {
                "name": "Quốc gia",
                "id": "Quốc gia"
            },
            {
                "name": "Số ca",
                "id": "Số ca",
                "type": "numeric",
                "format": {  
                    "specifier": ","
                }
            },
            {
                "name": "Tử vong",
                "id": "Tử vong",
                "type": "numeric",
                "format": {  
                    "specifier": ","
                }
            },
                        {
                "name": "Tỉ lệ tử vong",
                "id": "Tỉ lệ tử vong",
                "type": "numeric"
            }
        ],
        data=dff.to_dict('records'),
        editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode='multi',
        row_selectable='multi',
        row_deletable=False,
        selected_rows=[],
        page_action='native',
        page_current=0,
        page_size=10,
        style_header={
            'backgroundColor': '#CCE2CB',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(220, 220, 220)',
            }
        ],
    ),
    html.Div([
        html.P("Made by namnp"),
        html.P("For midterm Data Science")
    ])
])


@app.callback(
    Output('map', 'children'),
    [Input('datatable-row-ids', 'derived_virtual_data'),
     Input('datatable-row-ids', 'derived_virtual_selected_rows')]
)
def update_graphs(all_rows_data, slctd_row_indices):
    if slctd_row_indices is None:
        slctd_row_indices = []
    dff2 = pd.DataFrame(all_rows_data)
    borders = [5 if i in slctd_row_indices else 1
               for i in range(len(dff))]
    if "id" in dff2:
        return dcc.Graph(id='MW', figure=map_world(dff2).update_traces(marker_line_width=borders))


def map_world(dff2):
    """Return a graph about number of global covid-19 cases """

    fig = px.choropleth(data_frame=dff2, locations='id', locationmode='ISO-3',
                        color='Số ca',
                        hover_data=['Số ca', 'Tử vong'], hover_name="Quốc gia",
                        color_continuous_scale=px.colors.diverging.Tealrose,
                        color_continuous_midpoint=1000000,
                        range_color=[0, 40000000],
                        template='plotly')
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig



if __name__ == '__main__':
    app.run_server(debug=True)
