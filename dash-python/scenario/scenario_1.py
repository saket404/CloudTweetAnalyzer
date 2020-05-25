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

city_list = ['sydney','melbourne','brisbane','perth','adelaide','hobart']

def get_recent_scotty_city_tweets(df):
  # filter for recent tweets
  df['created_at'] = pd.to_datetime(df['created_at'], format = "%a %b %d %H:%M:%S +0000 %Y")
  start_date = pd.to_datetime('01 Sep 2018')
  df = df[df["created_at"] >= start_date]

  return df

def get_figure_3_sc1(df_scotty, aurin_variable_choice, aurin_variable_field):
  with open("data/aurin_data/Selected Average and Medians Census 2016/SA4_level.json" ,'r') as file:
        for line in file:
                data= json.loads(line)       
  records = []
  for record in data["features"]:
      records.append(record['properties'])
  aurin_data = pd.DataFrame(records)
    

  # filter aurin data just for major city SA4 areas
  pattern = re.compile("Sydney|Melbourne|Brisbane|Perth|Adelaide|Hobart")
  aurin_data = aurin_data[aurin_data['sa4_name16'].str.contains(pattern)].copy()
  aurin_data["city"] = aurin_data["sa4_name16"].apply(lambda x: re.search(pattern,x).group().lower())

  # print(aurin_data.columns)
  #get the median value of the SA4 areas in each city for the user selected AURIN variable
  median_aurin_variable = aurin_data.groupby("city")[aurin_variable_field].median()


  #put the AURIN variable in a copy of the df_scotty
  df_scotty_1 = df_scotty.copy()
  df_scotty_1[aurin_variable_field] = df_scotty_1.city.apply(lambda x: median_aurin_variable.loc[x])

  #get a montly time series for the average scotty sentiment, # tweets and median aurin variable by city
  df_time = df_scotty_1.groupby(['city', pd.Grouper(key='created_at', freq='M')]).agg({'sentiment_score':['mean','count'],aurin_variable_field:'median'})

  #reset index to get index as integer sequence 
  df_time.reset_index(inplace=True)
  #use the integer index to get a month count for the data for each city
  df_time['month'] = df_time.groupby(['city']).cumcount()+1

  #create new columns with the column names needed for the plot
  df_time["# tweets"] = df_time[('sentiment_score','count')]
  df_time[aurin_variable_choice] = df_time[(aurin_variable_field, 'median')]
  df_time["month"] = df_time[("month","")]
  df_time["sentiment score"] = df_time[("sentiment_score","mean")]
  df_time["city"] = df_time[("city","")]

    
  fig_animated_scatter = pexpr.scatter(df_time, x=aurin_variable_choice, y="sentiment score", animation_frame="month",
                size = "# tweets", color="city", hover_name="city", size_max=40, range_y=[-0.18,0.2], title="Average Sentiment Vs " + aurin_variable_choice)
    
  return fig_animated_scatter




def get_figures_sc1(df_scotty, aurin_variable_choice, aurin_variable_field):
#figure 1: number of monthly scotty tweets by city, line chart
#get timeseries dataframe with number of tweets for each month by city
    ts_df = df_scotty.groupby([pd.Grouper(key='created_at', freq='1M'),'city']).agg({"sentiment_score":len})
    ts_df.reset_index(inplace=True)
  #rename columns for what they need to be in plot
    ts_df.rename(columns = {"sentiment_score":"# tweets","created_at":"month"},inplace=True)
  
    fig_num_monthly = pexpr.line(ts_df, x='month', y= "# tweets", color="city", title="# Monthly Scott Morrison Tweets By City")
  
  
  
  
  #figure 2: average montly scotty sentiment by city, line chart

    ts_df= df_scotty.groupby([pd.Grouper(key='created_at', freq='1M'),'city']).agg({"sentiment_score":'mean'})
    ts_df.reset_index(inplace=True)
    ts_df.rename(columns = {"sentiment_score":"average sentiment","created_at":"month"},inplace=True)
    
    fig_average_sentiment = pexpr.line(ts_df, x='month', y= "average sentiment", color="city", title = "Average Monthly Scott Morrison Sentiment By City")
        
    
    
    
    
    #figure 3: average monthly scotty sentiment by city versus aurin variable selected by user
    #          achieved by plotting each month as a frame in an animation
    #          size of markers is #tweets

    #get AURIN SA4 data with selected Averages and Medians
    
    
    return fig_num_monthly, fig_average_sentiment