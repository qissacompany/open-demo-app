import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import datetime
import numpy as np

px.set_mapbox_access_token(st.secrets["mapbox"]['MAPBOX_client_token'])
mapbox_key = st.secrets["mapbox"]['MAPBOX_client_token']
my_style = st.secrets["mapbox"]['MAPBOX_qissa_default'] #..'MAPBOX_qissa_default' or 'MAPBOX_client_tiles' if set


def simulation_plot(sim_df,init_df=None,lin=0):
    #LOCAT
    yaxis_title_left = ['Vuosiasuntotuotanto (kem²)','Residential production (GFA)']
    yaxis_title_right = ['Asukasmäärä asuntokunnittain','Population by household']
    xaxis_title = ['Vuosi','Year']
    # translation of items
    col_translations = {
        'one-family-house':['Omakotitalot','One-family-house'],
        'multi-family-house':['Rivi/paritalot','Multi-family-house'],
        'apartment-condo':['Kerrostalot','Apartment-condo'],
        'families':['Perheissä asuvat','Family population'],
        'singles':['Yksin asuvat','Single population'],
        'other':['Muut','Other population']
    }

    #concat initial pop levels
    if init_df is None:
        init_year = sim_df['con_year'].min()
        data = {
            'con_year': [init_year-1],  # initial year
            'families': [0],  # initial count of families
            'singles': [0],   # initial count of singles
            'other': [0]  # initial count of others
        }
        init_df = pd.DataFrame(data)
    
    df = pd.concat([init_df, sim_df]).reset_index(drop=True)

    color_map = {
        'one-family-house': 'burlywood',
        'multi-family-house': 'peru',
        'apartment-condo': 'sienna'
    }

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    building_types = df['type'].unique()

    def get_histogram_bins(data):
        start = data.min() - 0.5  # Start half a year before the first year
        end = data.max() + 0.5    # End half a year after the last year
        return dict(start=start, end=end, size=1)

    def get_histogram_bins_old(data):
        start = data.min()
        end = data.max()
        if start == end:
            start -= 1.5
            end += 2.5
        else:
            end += 2  # Increase end by 1 to include the last data point
        return dict(start=start, end=end, size=1)

    for building_type in building_types:
        # Ensure building_type is a key in col_translations
        if building_type in col_translations:
            translated_name = col_translations[building_type][lin]
        else:
            translated_name = 'nan'  # Fallback if building_type is not found

        fig.add_trace(
            go.Histogram(
                name=translated_name,
                legendgroup='histo',
                x=df[df['type'] == building_type]['con_year'],
                y=df[df['type'] == building_type]['volume'],
                histfunc='sum',
                autobinx=False,
                xbins=get_histogram_bins(df[df['type'] == building_type]['con_year']),
                cumulative_enabled=False,
                marker=dict(color=color_map.get(building_type, 'brown'), opacity=0.9)
            ), secondary_y=False
        )
    fig.update_layout(barmode='stack')

    # ----------- POP LINES --------------

    # Calculate cumulative sums separately
    cumulative_data = {}
    for column in ['families', 'singles', 'other']:
        # Calculate cumulative sum, ensuring it only includes years with actual data
        cumulative_data[column] = df[df['volume'] > 0][column].cumsum()

    # Line plots for households
    lines = [('other', 'dot'), ('singles', 'dash'), ('families', 'solid')]
    for column, line_style in lines:
        # Get the cumulative data for the column
        column_cumulative_data = cumulative_data.get(column, [])

        fig.add_trace(
            go.Scatter(
                x=df[df['volume'] > 0]['con_year'],
                y=column_cumulative_data,
                mode='lines',
                name=col_translations[column][lin],
                legendgroup='lines',
                line=dict(color='black', width=1.0, dash=line_style),
                hoverinfo=None
            ), secondary_y=True
        )
    
    # Update axes
    year_now = datetime.datetime.now().year
    end_year = max(year_now, df['con_year'].max())

    # Create a range of years from the current year to the end year
    years_range = list(range(year_now, end_year + 1))

    # Update x-axis
    fig.update_xaxes(tickvals=years_range, ticktext=years_range,
                    range=[year_now - 0.5, end_year + 0.5],
                    title=xaxis_title[lin])

    #define first y-axis amx
    y1_max_value = df['volume'].max() * 1.2
    #define second y-axis max
    y2_max_value = max(np.cumsum(df['families']).max(), np.cumsum(df['singles']).max(), np.cumsum(df['other']).max())
    fig.update_yaxes(title=yaxis_title_left[lin], secondary_y=False, range=[0, y1_max_value])
    fig.update_yaxes(title=yaxis_title_right[lin], secondary_y=True, range=[0, y2_max_value])

    # Legend and layout
    fig.update_layout(
        margin={"r": 10, "t": 10, "l": 10, "b": 10}, height=700,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )

    return fig

def plot_masterplan_map(bu,net,hover_columns=None,zoom=14):
    lat = bu.unary_union.centroid.y
    lng = bu.unary_union.centroid.x

    #fig = go.Figure(go.Scattermapbox())

    fig = go.Figure(go.Scattermapbox(
        lat=bu.centroid.y,
        lon=bu.centroid.x,
        mode='markers',
        text=hover_columns,
        hoverinfo='text',
        marker=dict(
            opacity=0.1
        )
    ))
    if net is not None:
        fig.update_layout(
            mapbox={
                "layers": [  # https://plotly.com/python/reference/layout/mapbox/
                    {
                        "source": json.loads(bu.to_crs(4326).geometry.to_json()),
                        #"below": "traces",
                        "type": "line",
                        "color": "black",
                        "line": {"width": 0.5},
                    },
                    {
                        "source": json.loads(net.to_crs(4326).geometry.to_json()),
                        #"below": "traces",
                        "type": "line",
                        "color": "black",
                        "line": {"width": 0.5,"dash":[5,5]},
                    }
                ]
            }
        )
    else:
        fig.update_layout(
            mapbox={
                "layers": [  # https://plotly.com/python/reference/layout/mapbox/
                    {
                        "source": json.loads(bu.to_crs(4326).geometry.to_json()),
                        #"below": "traces",
                        "type": "line",
                        "color": "black",
                        "line": {"width": 0.5},
                    }
                ]
            }
        )
    
    #hover info
    if hover_columns:
        hover_data = bu[hover_columns].astype(str)
        hover_text = []
        for idx, row in hover_data.iterrows():
            hover_text.append('<br>'.join([f"{col}: {value}" for col, value in row.items()]))

        fig.data[0].text = hover_text
    
    # Set layout
    fig.update_layout(
        mapbox_style=my_style,
        mapbox_accesstoken=mapbox_key,
        mapbox=dict(
            center=dict(lon=lng, lat=lat),
            zoom=zoom
        ),
        margin=dict(l=10, r=10, t=10, b=10),
        height=650
    )
    return fig

def plot_footheat_map(point_gdf,weight_col,bu=None,net=None,zoom=14,scale=False,heat=True):

    # Normalize the centrality values to 0-1 scale for color mapping
    min_val = point_gdf[weight_col].min()
    max_val = point_gdf[weight_col].max()
    point_gdf['normalized_centrality'] = round((point_gdf[weight_col] - min_val) / (max_val - min_val),3)
    quantiles = point_gdf['normalized_centrality'].quantile([0.25, 0.5, 0.75]).to_list()

    if heat:
        # Define custom color scale with RGBA values for opacity
        custom_color_scale = [
            (0.00, "rgba(0, 0, 255, 0.0)"),   # Blue
            (quantiles[0], "rgba(0, 128, 0, 0.0)"),   # Green
            (quantiles[1], "rgba(255, 255, 0, 0.1)"), # Yellow
            (quantiles[2], "rgba(255, 165, 0, 0.5)"), # Orange
            (1.00, "rgba(255, 0, 0, 0.8)")    # Red
        ]
        lat = point_gdf.unary_union.centroid.y
        lng = point_gdf.unary_union.centroid.x
        fig = px.density_mapbox(point_gdf, 
                            lat=point_gdf.geometry.y, 
                            lon=point_gdf.geometry.x,
                            z=weight_col, 
                            radius=40,
                            center={"lat": lat, "lon": lng}, 
                            zoom=zoom,
                            width=1200,
                            height=700,
                            color_continuous_scale=custom_color_scale,
                            mapbox_style='carto-positron' # For the sake of this example, I'm using a public style.
                            )
    else:
        # Define custom color scale with RGBA values for opacity
        custom_color_scale = [
            (0.00, "rgba(0, 0, 255, 0.0)"),   # Blue
            (quantiles[0], "rgba(0, 128, 0, 0.0)"),   # Green
            (quantiles[1], "rgba(255, 255, 0, 0.1)"), # Yellow
            (quantiles[2], "rgba(255, 165, 0, 0.5)"), # Orange
            (1.00, "rgba(255, 0, 0, 0.8)")    # Red
        ]
        fig = px.scatter_mapbox(point_gdf, 
                                lat='lat', 
                                lon='lon',
                                size=weight_col, 
                                color=weight_col,
                                color_continuous_scale=custom_color_scale,
                                size_max=25, 
                                zoom=zoom,
                                mapbox_style=my_style)
    
    
    fig.update_layout(coloraxis_showscale=scale,margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=700)
    if bu is not None:
        fig.update_layout(
            mapbox={
                "layers": [  # https://plotly.com/python/reference/layout/mapbox/
                    {
                        "source": json.loads(bu.to_crs(4326).geometry.to_json()),
                        #"below": "traces",
                        "type": "line",
                        "color": "black",
                        "line": {"width": 0.5},
                    },
                    {
                        "source": json.loads(net.to_crs(4326).geometry.to_json()),
                        #"below": "traces",
                        "type": "line",
                        "color": "black",
                        "line": {"width": 0.5,"dash":[5,5]},
                    }
                ]
            }
        )
    return fig
