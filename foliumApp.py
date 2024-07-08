import folium.features
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# PREAMBLE

APP_TITLE = "Fraud and Identity Theft Report"
APP_SUBTITLE = "Source: Federal Trade Commission"

# DEFINE HERLPER FUNCTIONS

def display_fraud_facts(df, year, quarter, state_name, report_type, field_name, metric_title, number_format = '${:,}', is_median = False):
    df = df[(df['Year'] == year) & (df['Quarter'] == quarter) 
            & (df['Report Type'] == report_type)]
    
    if state_name:
        df = df[df['State Name'] == state_name]

    df.drop_duplicates(inplace = True)

    if is_median:
        total = df[field_name].mean()
    else:
        total = df[field_name].sum()

    st.metric(metric_title, number_format.format(round(total)))
    return None

def display_map(df, year, quarter):
    df = df[(df['Year'] == year) & (df['Quarter'] == quarter)]
    
    map = folium.Map(location=[38, -96.5], zoom_start=4, scrollWheelZoom = False, tiles='CartoDB positron')
    
    choropleth = folium.Choropleth(
        geo_data='./data/us-state-boundaries.geojson',
        data = df,
        columns = ('State Name', 'State Total Reports Quarter'),
        key_on= 'feature.properties.name',
        line_opacity=0.8,
        highlight=True
    )
    choropleth.geojson.add_to(map)

    df = df.set_index('State Name')
    state_name = 'North Carolina'
    # st.write(df.loc[state_name, 'State Pop'][0])

    for feature in choropleth.geojson.data['features']:
        state_name = feature['properties']['name']
        if state_name in df.index:
            population = df.loc[state_name, 'State Pop'][0]
            formatted_population = "Population: {:,}".format(population)
        else:
            formatted_population = "Population: N/A"
        feature['properties']['population'] = formatted_population

        if state_name in df.index:
            reports = df.loc[state_name, 'Reports per 100K-F&O together'][0]
            formatted_reports = "Reports: {:,}".format(round(reports))
        else:
            formatted_reports = "Reports: N/A"
        feature['properties']['reports'] = formatted_reports

    choropleth.geojson.add_child(
        folium.features.GeoJsonTooltip(['name', 'population', 'reports'], labels=False)
    )

    st_map = st_folium(map, width = 700, height = 450)

    state_name = ''
    if st_map['last_active_drawing']:
        state_name = st_map['last_active_drawing']['properties']['name']

    return state_name

def display_time_filters(df):
    year_list = list(df['Year'].unique())
    year_list.sort(reverse=True)
    year = st.sidebar.selectbox('Year', year_list)
    quarter = st.sidebar.radio('Quarter', [1,2,3,4])
    return year, quarter

def display_state_filter(df, state_name):
    state_list = [''] + list(df['State Name'].unique())
    state_list.sort()
    state_index = state_list.index(state_name) if state_name and state_name in state_list else 0
    state_name = st.sidebar.selectbox('State', state_list, state_index)
    return state_name

def display_report_types():
    report_types = ['Fraud', 'Other']
    return st.sidebar.radio('Report Type', report_types)

def main():
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon="🧊"
        )
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)

    # LOAD DATA
    geodata = gpd.read_file('./data/us-state-boundaries.geojson')
    df_continental = pd.read_csv('./data/AxS-Continental_Full Data_data.csv')
    df_fraud = pd.read_csv('./data/AxS-Fraud Box_Full Data_data.csv')
    df_median = pd.read_csv('./data/AxS-Median Box_Full Data_data.csv')
    df_loss = pd.read_csv('./data/AxS-Losses Box_Full Data_data.csv')

    report_type = 'Fraud'

    # DISPLAY FILTERS AND MAP

    year, quarter = display_time_filters(df_continental)
    state_name = display_map(df_continental, year, quarter)
    state_name = display_state_filter(df_continental, state_name)
    report_type = display_report_types()
    
    # DISPLAY METRICS

    st.subheader(f'{year} Q{quarter} {state_name} {report_type} Report Facts')
    c1, c2, c3 = st.columns(3)
    with c1:
        display_fraud_facts(df_fraud, year, quarter, state_name, report_type, 'State Fraud/Other Count', f'\# of {report_type} Reports', number_format='{:,}')
    with c2:
        display_fraud_facts(df_median, year, quarter, state_name, report_type, 'Overall Median Losses Yr', f'Median Dollar Losses', is_median=True)
    with c3:
        display_fraud_facts(df_loss, year, quarter, state_name, report_type, 'Total Losses', f'Total Dollar Losses')

if __name__ == "__main__":
    main()