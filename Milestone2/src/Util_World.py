import json
import bz2
import sys
import os
import numpy as np
import pandas as pd
from chart_studio import plotly
import plotly.graph_objs as go
import matplotlib.pyplot as plt
import seaborn as sns
from geopy.geocoders import Nominatim
import plotly.express as px

def add_parties(quotes_world,catalogue):
    '''
    take as input a dataframe containing the quotations with their qid speaker and mentions.In addition of the catalogue
    containing information about the us politicians. return the same dataframe but with the correspondant parties of the qids
    '''
    part=pd.DataFrame()
    for i,qid in enumerate(quotes_world.qids):
        party=[catalogue[catalogue['qid'] == qid].parties.tolist()]
        part=part.append(party,ignore_index=True)
    quotes_world['party']=part
    return quotes_world


def extract_individual_quotes(original):
    '''
    take as input a dataframe containing quotations mentioning one or multiple politicians, it returns quotations mentioning only 
    one politician (if one quote mentions 2 persons, returns 2 quotes each one mentioning only 1)
    '''
    mentions=pd.DataFrame()
    for i,row in original.iterrows():
        for j,mention_qid in enumerate(row.mentions_qids):
            mention=pd.Series([row.quoteID,row.qids,row.speaker,mention_qid,row.mentions[j],row.country[j],row.party,row.sentiment])
            mentions=mentions.append(mention,ignore_index=True)
    mentions.rename(columns={0:'quoteID',1:'qid',2:'mention_qid',3:'mentioned',4:'speaker',5:'country',6:'party',7:'sentiment'},inplace=True)
    print(f'from : {len(original)} mentioning quotes, we obtain {len(mentions)} mentions.')
    return mentions


def geolocalisation(mentions):
    '''
    take as input dataframe with different countries, return the localisation of the countries
    '''
    geolocator = Nominatim(user_agent="my_user_agent")
    geoloc=pd.DataFrame()
    countr=mentions.groupby(['country'])
    for i,count in enumerate(countr.indices):
        geo=geolocator.geocode(count)[1]
        geoloc=geoloc.append({'lat':geo[0],'lon':geo[1]},ignore_index=True)
    geoloc.index=countr.indices
    geoloc.head()
    return geoloc

def years_parse(group_by_years,geolocs,years):
    '''
    take as input dataframe grouped by years, geolocalisation of different countries and thes years contained in dataframe.
    return values for graph : geolocalisation, mean of frequencies, sentiment and values during the years from countries
    '''
    countries_by_year=pd.DataFrame()
    for y in years:
        y1=group_by_years.get_group(y)
        y2=y1.groupby(['country'])
        freq= (y2.count().qid-y2.count().qid.min())/(y2.count().qid.max()-y2.count().qid.min())#normalized by min/max 
        lat=[]
        lon=[]
        sent=(y2.mean().sentiment-y2.mean().sentiment.min())/(y2.mean().sentiment.max()-y2.mean().sentiment.min())#normalized by min/max 
        for i,count in enumerate(y2.indices):
            lat.append(geolocs.loc[count,'lat'])
            lon.append(geolocs.loc[count,'lon'])
        countries=pd.DataFrame({'country':freq.index,'freq':freq.values,'year':y,'lat':lat,'lon':lon, 'sentiment':sent})
        countries_by_year=countries_by_year.append(countries,ignore_index=True)
    return countries_by_year

def plotly_graph_world(world,democ,repub,years,locO):
    '''
    takes as input dataframes already grouped by years, a array containing the different years and the 
    geolocalisation of the origin of edges. Return a interactive plot,
    with a dropdown button allowing to visualising the 3 different dataframes and a slider allowing to      decide wich year visualize
    '''
    geolocator = Nominatim(user_agent="my_user_agent")
    locO = geolocator.geocode('USA')
    #we give data separated by years already
    parti=[]#parties
    Figures=[] #all the traces and figures 
    years_a=[] #years 
    for i,year in enumerate(years) : 
    #extract the data by year
        y=world.get_group(year)
        yd=democ.get_group(year)
        yr=repub.get_group(year)
        #add the choropleth for each year from all the USA quotes
        Figures.append(go.Choropleth(coloraxis='coloraxis',
                                          z=y['sentiment'],
                                          locations=y['country'],
                                          locationmode='country names',
                                          hoverinfo='location + z',
                                          visible=True
                                    ))
        #add labels for year and parties
        parti.append('All')
        years_a.append(year)
        #add the lines for each year (all quotes)
        for j,country in y.iterrows():
            Figures.append(go.Scattergeo(
                             lat=[locO[1][0],country.lat], 
                             lon=[locO[1][1],country.lon],
                             mode='lines+markers',
                             name='All',
                             hovertext=country.country+' freq ='+str(country.freq),
                             line=dict(width=country.freq*10, color='grey'),
                             visible=True,
                             showlegend=False
            ))
            parti.append('All') #add labels for year and parties
            years_a.append(year)
        #now for democratic party
        Figures.append(go.Choropleth(coloraxis='coloraxis',
                                         z=yd['sentiment'],
                                         locations=yd['country'],
                                         locationmode='country names',
                                         hoverinfo='location + z',
                                         visible=False
                                    ))
        #add label
        parti.append('Democ')
        years_a.append(year)
        for j,country in yd.iterrows():
            Figures.append(go.Scattergeo(
                             lat=[locO[1][0],country.lat], 
                             lon=[locO[1][1],country.lon],
                             mode='lines+markers',
                             name='All',
                             hovertext=country.country+' freq ='+str(country.freq),
                             line=dict(width=country.freq*10, color='blue'),
                             visible=False,
                             showlegend=False
            ))
            parti.append('Democ')
            years_a.append(year)
        #now for republican 
        Figures.append(go.Choropleth(coloraxis='coloraxis',
                                          z=yr['sentiment'],
                                          locations=yr['country'],
                                          locationmode='country names',
                                          hoverinfo='location + z',
                                         visible=False
                                    ))
        parti.append('Repub')
        years_a.append(year)
        for j,country in yr.iterrows():
            Figures.append(go.Scattergeo(
                             lat=[locO[1][0],country.lat], 
                             lon=[locO[1][1],country.lon],
                             mode='lines+markers',
                             name='All',
                             hovertext=country.country+' freq ='+str(country.freq),
                             line=dict(width=country.freq*10, color='red'),
                             visible=False,
                             showlegend=False
            ))
            parti.append('Repub')
            years_a.append(year)
    #we create the layout of the graph
    layout = go.Layout(margin={"r":0,"t":50,"l":0,"b":100}, #marges
                       mapbox_style="carto-positron",
                       title="World map USA politician distribution",title_x=0.52,title_y=0.95, #title
                       showlegend=False,hovermode='closest',height=600
                )
    fig=go.Figure(data=Figures,layout=layout)#creation of the graph
    fig.update_geos(
        visible=True, resolution=110,projection=dict(type="natural earth"),
        showcountries=True, countrycolor="Black",
        showsubunits=True, subunitcolor="Blue"
    )
    #add the colorscale
    fig.update_coloraxes(
        colorbar=dict(title='sentiment'),
        colorscale='RdBu'
    )
    #steps for the different sliders
    steps=[]
    steps2=[]
    steps3=[]
    for year in years:
        step=dict(
            method='update',
            label=year,
            args=[{"visible": [(a==year)&(parti[i]=='All') for i,a in enumerate(years_a)]},
                      {"title": "World map USA politician distribution in : " + year}] 
            )
        steps.append(step)
        step2=dict(
            method='update',
            label=year,
            args=[{"visible": [(a==year)&(parti[i]=='Democ') for i,a in enumerate(years_a)]},
                      {"title": "World map Democratic distribution : " + year}] 
            )
        steps2.append(step2)
        step3=dict(
            method='update',
            label=year,
            args=[{"visible": [(a==year)&(parti[i]=='Repub') for i,a in enumerate(years_a)]},
                      {"title": "World map Republican distribution : " + year}] 
            )
        steps3.append(step3)
    #creation of sliders
    sliders = [dict(
            active=0,
            currentvalue={"prefix": "All: "},
            pad={"t": 0},
            steps=steps,
            visible=True

        ),dict(
            active=0,
            currentvalue={"prefix": "Democratic: "},
            pad={"t": 0},
            steps=steps2,
            visible=False

        ),dict(
            active=0,
            currentvalue={"prefix": "Republican: "},
            pad={"t": 0},
            steps=steps3,
            visible=False

        )
        ]
    #addition of sliders to graph
    fig.update_layout(
            sliders=sliders
        )
    #creation of dropdown buttons
    updt=[]
    updt.append(dict(buttons=list([dict(args=[{'visible':[(a=='2015')&(parti[i]=='All') for i,a in enumerate(years_a)]},
                                              {"title":"World map USA politician distribution in : 2015",
                                                    'sliders[0].visible': True,'sliders[0].active':0, #active the current slide
                                                     'sliders[1].visible': False,'sliders[2].visible':False #hide the others
                                                }],   
                                            label='All',
                                            method="update"

                                             ),

                                   dict(args=[{'visible':[(a=='2015')&(parti[i]=='Democ') for i,a in enumerate(years_a)]},
                                              {"title":"World map Democratic distribution in : 2015",'sliders[1].visible': True,'sliders[1].active':0,#active current slide
                                               'sliders[0].visible': False,'sliders[2].visible':False #hide the others
                                              } ], label='Democratic',
                                        method="update"
                                       ),
                                   dict(args=[{'visible':[(a=='2015')&(parti[i]=='Repub') for i,a in enumerate(years_a)]},
                                              {"title":"World map Republican distribution in : 2015",'sliders[2].visible': True,'sliders[2].active':0,
                                              'sliders[0].visible': False,'sliders[1].visible':False #hide the others
                                              }], label='Republican',
                                       method="update"
                                       )
                                      ]))) 


    fig.layout.updatemenus=updt
    return fig