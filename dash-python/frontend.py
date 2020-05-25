import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd

###### Import scenario backend
import scenario.scenario_1 as sc1
import scenario.scenario_2 as sc2
import scenario.scenario_3 as sc3
import time
import configparser
###### Import couchdb backend
import couchdb_connector.couchdb_backend as cdb

### Config reader
config = configparser.ConfigParser()
config.read('config.ini')
couchConfig = config['couch']

# Scenario keywords
sc_1 = ['city','sentiment_score','user']
sc_2 = ['city','sentiment','hashtags','user']
sc_3 = ['city', 'full_text','sentiment_score','user','coordinates']

## Aurin mapping dropdown



###################

dropdown_mapping = [
            {'label':"Median Age",'value': "median_age_persons"},
            {'label':"Median Weekly Total Household Income",'value': "median_tot_hhd_inc_weekly"},
            {'label':"Median Weekly Family Income" ,'value': "median_tot_fam_inc_weekly"},
            {'label':"Median Weekly Personal Income" ,'value': "median_tot_prsnl_inc_weekly"},
            {'label':"Median Monthly Mortgage Repayment",'value' : "median_mortgage_repay_monthly"},
            {'label':"Median Weekly Rent",'value' : "median_rent_weekly"},
            {'label':"Average Number of Persons Per Bedroom" ,'value': "average_num_psns_per_bedroom"},
            {'label':"Average Household Size" ,'value': "average_household_size"}]

###################

#### Connect to database
db_obj = cdb.db_instance(couchConfig['url'])


## Get dataframe associate of each scenario
df_1 = pd.DataFrame(cdb.query_view(db_obj,sc_1,'scomo',couchConfig['view']))
df_2 = pd.DataFrame(cdb.query_view(db_obj,sc_2,'corona',couchConfig['view']))
df_3 = pd.DataFrame(cdb.query_view(db_obj,sc_3,'politics',couchConfig['view']))




################ Scenario 1
#get the scotty tweets since Sep 2018 that fall in the cities in city_list
df_1 = sc1.get_recent_scotty_city_tweets(df_1)
fig_num_monthly, fig_average_sentiment = sc1.get_figures_sc1(df_1, dropdown_mapping[0]['label'], dropdown_mapping[0]['value'])


##Scenario 2
corona_timeseries,corona_htcount = sc2.get_corona_figure(df_2)
##Scenario 3
df_3 = df_3[df_3.coordinates.apply(sc3.check_melb)]
tmp_1,tmp_2,tmp_3 = sc3.get_politic_melb_df(df_3)
fig_map,fig_cor,fig_pie,fig_timeline = sc3.get_figures_sc3(tmp_1,tmp_2,tmp_3,df_3)



external_stylesheets = [
    # 'https://codepen.io/chriddyp/pen/bWLwgP.css',
    'assets/s1.css']
app=dash.Dash(__name__,external_stylesheets=external_stylesheets)
app.title='Twitter Analysis'


# Process all keys value in dropdown_mapping before run to reduce time loading
fig_sc1={}
for i in dropdown_mapping:
    fig_animated_scatter=sc1.get_figure_3_sc1(df_1, i['label'], i['value'])
    fig_sc1[i['value']]=fig_animated_scatter

app.layout=html.Div(
                children=[
                        html.H1('Twitter analysis by Dash',style={ 'textAlign': 'center'},className='title'),
                        dcc.Tabs(id="tabs", value='tab-1', children=[
                            dcc.Tab(label='Scenario 1',children=[
                            html.Div([
                                html.Div(children=[
                                    html.Div(children=[(
                                        html.Div([ html.H4('Choose aurin data to correlate'),
                                                dcc.Dropdown(id = 'aurin_data_sc1',
                                                options=dropdown_mapping,value=dropdown_mapping[0]['value'])
                                                ],className='pretty_container eight columns'
                                                )
                                            ),
                                            html.Div(
                                                [html.H6(f'{len(df_1)}'), html.P("No. of Tweets")],
                                                className="mini_container two columns",
                                            ),
                                            html.Div(
                                                [html.H6(f'{df_1["user"].nunique()}'), html.P("No. of Users")],
                                                className="mini_container two columns",
                                            )
                                        ]
                                    ,className='row container-display'),
                                    
                                html.Div([
                                    dcc.Graph(id='fig_animated_scatter')
                                ],className='pretty_container twelve columns')]),

                                ]),

                        html.Div([
                            dcc.Graph(figure=fig_num_monthly,style={"width":"50%",'display': 'inline-block'}),
                            dcc.Graph(figure=fig_average_sentiment,style={"width":"50%",'display': 'inline-block'})  
                        ],className='pretty_container twelve columns'),
                        ],className='twelve columns'),                   
                        
                        dcc.Tab(label="Scenario 2", value='tab-2', children=[                   
                        html.Div(children=[
                                    html.Div(
                                                [html.H6(f'{len(df_2)}'), html.P("No. of Tweets")],
                                                className="mini_container two columns",
                                            ),
                                            html.Div(
                                                [html.H6(f'{df_2["user"].nunique()}'), html.P("No. of Users")],
                                                className="mini_container two columns",
                                            )],className='row container-display'),
                        html.Div([
                        dcc.Graph(figure=corona_timeseries,style={'width':'800', 'height':'400'})],className='pretty_container twelve columns'),
                        dcc.Graph(figure=corona_htcount,style={'width':'100%'},className='pretty_container twelve columns')
                        ],className='twelve columns'),
                        
                        dcc.Tab(label="Scenario 3", value='tab-3', children=[                   
                        html.Div(children=[
                            html.Div(
                                    [html.H6(f'{len(df_3)}'), html.P("No. of Tweets")],
                                    className="mini_container two columns",
                                    ),
                                    html.Div(
                                            [html.H6(f'{df_3["user"].nunique()}'), html.P("No. of Users")],
                                                className="mini_container two columns",
                                            )],className='row container-display'),
                            
                        dcc.Graph(figure=fig_map,style={'autosize':True},className='pretty_container twelve columns')
                        ,
                        html.Div(
                            [
                            dcc.Graph(figure=fig_cor,style={'width':'60%','autosize':True,'display': 'inline-block'}),
                            dcc.Graph(figure=fig_pie,style={'width':'40%','autosize':True,'display': 'inline-block'}),
                            ],className='pretty_container twelve columns'),
                        dcc.Graph(figure=fig_timeline,style={'width':'100%','autosize':True},className='pretty_container twelve columns')
                        ],className="twelve columns")
                    ])
],className='twelve columns')
# ],className='twelve columns')


@app.callback(
    Output('fig_animated_scatter', 'figure'),
    [Input('aurin_data_sc1', 'value')])
def update_sc1_plot(aurin_data_sc1):
    return fig_sc1[aurin_data_sc1]


if __name__=='__main__':
    app.run_server(debug=False,threaded=True)


