import json
import pandas as pd
from collections import Counter
from collections import defaultdict
import re
import numpy as np
import scipy
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


def get_corona_figure(df_2):
    df_2['sentiment_score'] = df_2.sentiment.apply(lambda x: x['compound'])
    df_2['created_at'] = pd.to_datetime( df_2['created_at'], format= "%a %b %d %H:%M:%S +0000 %Y")
    df_2 = df_2[(df_2['created_at'] > '2020-01-01 0:00:00')]

    ht_counter = Counter()
    for i in df_2['hashtags'].to_list():
        for j in i:
            ht_counter[j] += 1

    df_2 = df_2[['created_at','city','sentiment_score']]
    
    df_2 = df_2.groupby(['city', pd.Grouper(key='created_at', freq='W')]).agg({'sentiment_score': ['mean','count']})
    df_2 = df_2.reset_index(level=[0,1])
    df_2.columns = ['city','created_at','sentiment','tweet_count']
    df_2.reset_index()
    df_2['week'] = df_2.groupby(['city']).cumcount()+1
    df_2 = df_2[df_2['week'] < 19]
    
    aurin_data_file = "data/aurin_data/Selected Average and Medians Census 2016/SA4_internet.json"
    corona_aurin = gpd.read_file(aurin_data_file)
    city_regex = re.compile("(perth)|(brisbane)|(melbourne)|(sydney)|(adelaide)")
    corona_aurin['city'] = corona_aurin['sa4_name16'].apply(
        lambda x: city_regex.search(x.lower()).group(0) if city_regex.search(x.lower()) else "")
    corona_aurin = corona_aurin[corona_aurin['city'].isin(['perth','sydney','melbourne','adelaide','brisbane'])]
    corona_aurin = corona_aurin.groupby(['city'],as_index=False).agg({'access_net_home_net_acsd_dwl_pr100': ['mean'],})
    corona_aurin.columns = ['city','internet_access']
    df_2 = pd.merge(df_2, corona_aurin, on='city', how='outer')

    corona_timeseries = pexpr.scatter(df_2, x="internet_access",
                                      y="sentiment",
                                      animation_frame="week",
                                      size="tweet_count",
                                      color="city",
                                      labels= {"sentiment": "Sentiment Score", "internet_access": "Percentage Population access to Internet", "city": "City"},
                                      hover_name="city",
                                      range_y=[-0.18,0.2])
    
    ht_data = {'Hashtags': [],'Count': []}
    for i in ht_counter.most_common(15):
        ht_data['Hashtags'].append(i[0])
        ht_data['Count'].append(i[1])
    corona_htcount = pexpr.bar(ht_data, x='Hashtags',y='Count',text='Count')
    corona_htcount.update_traces(textposition='outside')
    corona_htcount.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

    return corona_timeseries,corona_htcount

