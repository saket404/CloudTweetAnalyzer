#
# Team 43, Melbourne
# Aidan McLoughney(1030836)
# Thanaboon Muangwong(1049393)
# Nahid Tajik(1102790)
# Saket Khandelwal (1041999)
# Shmuli Bloom(982837)
#

import json
import pandas as pd
from collections import Counter
from collections import defaultdict
import re
import geopandas as gpd #for reading aurin data into dataframe
import plotly as px
from datetime import datetime, timedelta
from email.utils import parsedate_tz
from shapely.geometry import Point,box
import plotly.graph_objs as go
import textwrap
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from plotly.offline import iplot
import plotly.express as pexpr
import warnings
warnings.filterwarnings("ignore")

def check_melb(coordinates):
    if not coordinates:
        return False
    c = coordinates['coordinates']
    p = Point(float(c[0]),float(c[1]))
    greater_melb = box(144.3336,-38.5030,145.8784,-37.1751)
    if greater_melb.contains(p):
        return True
    else:
        return False


def get_politic_melb_df(df_original):
    
    df = df_original.copy()

    #create a geopandas dataframe to for the surburb, suburb code and shapely polygon objects from the aurin data
    aurin_data_file = "data/aurin_data/Selected Average and Medians Census 2016/data1552693085116145970.json"
    gdf = gpd.read_file(aurin_data_file)
    
    suburb_polygons = gdf['geometry'].to_list()
    suburb_names = gdf['feature_name'].to_list()
    suburb_codes = gdf["feature_code"].to_list()

    def get_suburb_point(coordinates):
        point = Point(coordinates)
        for i, suburb in enumerate(suburb_polygons):
            if suburb.contains(point):
                return pd.Series((suburb_names[i],suburb_codes[i]),index=['suburb','suburb_code'])

    # add suburb name and code columns to tweet docs df

    df.rename(columns = {"coordinates":'coordinates_object'},inplace=True)
    #extract the (lon,lat) coordinates from the coordinates object
    df['coordinates'] = df['coordinates_object'].apply(lambda x: x['coordinates'])
    # print(df.head())
    # df[['suburb','suburb_code']]  = df.apply(lambda x: get_suburb_point(x['coordinates']),axis=1)
    df[['suburb','suburb_code']]  = df.apply(lambda x: get_suburb_point(x['coordinates']),axis=1)
    
    
    ## get the mean sentiment score for each suburb, this will be the color on the choropleth map
    df_choro = df[['suburb','sentiment_score']]
    df_choro = df_choro.groupby(['suburb'],as_index=False).agg({'sentiment_score': ['mean','count']})
    df_choro.columns = ['suburb','sentiment_score','tweet_count']
    df_choro.reset_index()
    df_choro = df_choro[['suburb','sentiment_score','tweet_count']]
    
    #filter for suburbs that have at least tweet_count_min number of tweets
    tweet_count_min  = 25
    df_choro = df_choro[df_choro['tweet_count'] > tweet_count_min]
    chosen_sub = df_choro['suburb'].to_list()
    
    
    df = df[df['suburb'].isin(chosen_sub)]
    df[['lon','lat']] = df['coordinates'].apply(lambda x: pd.Series((x[0],x[1]),index=['lon','lat']))
    
    

    return df_choro,df,gdf


def get_figures_sc3(df_choro,df,gdf,df_3):
    
    aurin_data_file = "data/aurin_data/Selected Average and Medians Census 2016/data1552693085116145970.json"
    with open(aurin_data_file,'r') as file:
        geojsdata= json.load(file)
        
    mapboxt = 'pk.eyJ1Ijoic2FibG80MSIsImEiOiJja2FhaWxiOGgwMzM2MnlvYmtpdDFyNDlxIn0.zaSp8Ui7eS0UtuE6ImpzeQ' #my mapbox_access_token 

    choro = go.Choroplethmapbox(z=df_choro.sentiment_score,
                                locations = df_choro.suburb,
                                featureidkey = 'properties.feature_name',
                                colorscale = 'bluered_r', # cartoz
                                colorbar = dict(thickness=20, ticklen=3, title={'text':'Sentiment Score', 'font':{'size':14}}),
                                geojson = geojsdata,
                                marker_opacity=0.5,
                                hovertemplate = '<b>Suburb</b>: <b>%{properties.feature_name}</b>'+
                                                '<br><b>Average Sentiment </b>: %{z}<br>')

    scatt = go.Scattermapbox(lat=df.lat,lon=df.lon,mode='markers+text',
                             hovertext=df.full_text.apply(lambda txt: '<br>'.join(textwrap.wrap(txt, width=50))),
                             below='',marker=dict( size=6, color ='rgb(235, 0, 100)'))
    layout_1 = go.Layout(title_text ='Melbourne Political Sentiment',
                       title_x =0.5, titlefont={"size":25},
                    #    width=2000, height=1000
                    #   width=750,
                    height=800,
                       mapbox = dict(center= dict(lat=-37.815008, lon=144.960631),
                                     accesstoken= mapboxt,zoom=10,style="light"))
    fig_map = go.Figure(data=[choro,scatt], layout =layout_1)
    
    
    
    gdf_s = gdf[gdf['feature_name'].isin(df_choro.suburb.to_list())]
    aurin_correlation_df = gdf_s.set_index("feature_name").join(df_choro.groupby("suburb")['sentiment_score'].mean())
    aurin_correlation_df['size'] = 5

    fig_cor = pexpr.scatter(aurin_correlation_df, x="median_rent_weekly", y="sentiment_score", color="sa2_name16",
                 size= 'size',
                 labels= {"sentiment_score": "Sentiment Score", "median_rent_weekly": "Median Weekly Rent ($)", "sa2_name16": "Suburb"},
                 hover_data =['sa2_name16','sentiment_score',"median_rent_weekly"])
    fig_cor.update_layout(
        title={
            'text': "Average Suburb Sentiment vs. Median Weekly Rent",
            'y':0.95,
            'x':0.45,
            'xanchor': 'center',
            'yanchor': 'top'})

    
    data = [go.Pie(labels=df_choro.suburb, values=df_choro.tweet_count, hole=0.2, textinfo="label+value", textposition="inside")]
    layout_2 = go.Layout(title_text ='Number of Locatable Tweets by Suburb', title_x =0.5 )#, width=1000, height=750)
    fig_pie = go.Figure(data=data, layout=layout_2)
    
    
    df_3['created_at'] = pd.to_datetime(df_3['created_at'], format= "%a %b %d %H:%M:%S +0000 %Y")
    df_t = df_3.set_index("created_at")
    df_t["# tweets"] = 1
    monthly_tweets  = df_t.resample('1M')['# tweets'].sum()
    monthly_tweets = monthly_tweets.to_frame(name='# tweets')
    monthly_tweets['Date'] = monthly_tweets.index

    fig_timeline = pexpr.line(monthly_tweets, x='Date', y='# tweets', title= "Monthly Political Tweets in Melbourne with Exact Locations")

    significant_dates = ['2013-09-30','2014-11-30','2015-02-28','2018-11-30','2019-05-31','2020-01-31']
    significant_events = ['Australian Federal <br> Election  2013', 'Victorian State Election 2014', 
                          "Liberal Party <br> Leadership Spill", "Victorian State Election 2018", "Australian Federal <br> Election 2019",
                          "Victorian Bushfires 2019/20" ]

    for i in range(len(significant_dates)):
        fig_timeline.add_annotation( # add a text callout with arrow
        text=significant_events[i], x=pd.to_datetime(significant_dates[i]),
                                y=monthly_tweets.loc[significant_dates[i],'# tweets'], arrowhead=1, showarrow=True)


    return fig_map,fig_cor,fig_pie,fig_timeline
    
