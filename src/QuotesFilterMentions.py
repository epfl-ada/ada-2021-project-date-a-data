import json
import bz2
import sys
import os
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np
import re
from urllib.parse import urlparse
from pandas.io.json import json_normalize
from qwikidata.sparql import (get_subclasses_of_item,return_sparql_query_results)



def generate_patterns(WIKI_DATA_FILTERED_LABELED,US=True):
    '''
    Take as input the filtered wikidata with interpretations, return a pattern containing all names of US politician
    '''
    politician_df=pd.read_json(WIKI_DATA_FILTERED_LABELED, lines=True)
    if US:
        politician_df = politician_df[politician_df['nationality']=='Q30'] #extract US politicians
        names_us = politician_df[['qid','name','aliases']] #extract qid, name, aliases
        names_us['aliases_all'] = [a+[b] for a,b in zip(names_us['aliases'],names_us['name'])]
        names_flat = names_us.explode('aliases_all')
    else:
        sparql_query = """
        SELECT DISTINCT ?countryLabel ?hgovernmentLabel ?hstateLabel
        WHERE
        {
        ?country wdt:P31 wd:Q3624078 .
        ?country p:P6 ?statement .    
        ?statement ps:P6 ?hgovernment .
        ?country wdt:P6 ?hgovernment .
        ?country wdt:P35 ?hstate .
        #not a former country
        FILTER NOT EXISTS {?country wdt:P31 wd:Q3024240}
        #and no an ancient civilisation (needed to exclude ancient Egypt)
        FILTER NOT EXISTS {?country wdt:P31 wd:Q28171280}
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
        }
        ORDER BY ?countryLabel
        """
        res = return_sparql_query_results(sparql_query)
        country_list = json_normalize(res["results"]["bindings"])
        name_list = country_list['hgovernmentLabel.value'].tolist() + country_list['hstateLabel.value'].tolist()
        politician_df = politician_df[politician_df['name'].isin(name_list)]
        names_us = politician_df[['qid','name','aliases']] #extract qid, name, aliases
        names_us['aliases_all'] = [a+[b] for a,b in zip(names_us['aliases'],names_us['name'])]
        names_flat = names_us.explode('aliases_all')
        hstate = country_list[['countryLabel.value','hstateLabel.value']].rename(columns={'countryLabel.value':'country','hstateLabel.value':'name'})
        hgov = country_list[['countryLabel.value','hgovernmentLabel.value']].rename(columns={'countryLabel.value':'country','hgovernmentLabel.value':'name'})
        hhead = pd.concat([hstate,hgov]).drop_duplicates()
        hhead = hhead[~hhead.name.str.contains("Joe Biden")]
        names_flat = names_flat.merge(hhead, how='inner', left_on='name', right_on='name')
    pattern_list = names_flat['aliases_all'].tolist()
    pattern_list = [x for x in pattern_list if len(x)>=4 and'(' not in x and '?' not in x and '*' not in x and '+' not in x and '{' not in x and '|' not in x and '[' not in x]
    # pattern_list1 = [x for x in pattern_list if len(x)<=4 and '(' not in x and '?' not in x and '*' not in x and '+' not in x and '{' not in x and '|' not in x and '[' not in x]
    pattern = '|'.join(pattern_list)
    # pattern += '|(?<![\w\d])' + '(?![\w\d])|(?<![\w\d])'.join(pattern_list1) + '(?![\w\d])'
    pattern = pattern.replace("(", "").replace(")", "").replace("?", "")
    return pattern,names_flat

def filter_mentions(QUOTES_BY_US,pattern,QUOTE_MENTIONS, verbose = False):
    '''
    Take as input the quotes said by US politicians, return all quotes containing politician names/aliases
    '''
    #extraction of political name's mention from the quotes
    CHUNKSIZE=10000
    try:
        os.remove(QUOTE_MENTIONS)
    except:
        pass
    total_time,total_mentions,chunk_number,nb_quote=0,0,0,0
    mentions=[]
    with bz2.open(QUOTE_MENTIONS, 'wb') as bzout_mention_usa:
        with pd.read_json(QUOTES_BY_US, lines=True, chunksize=CHUNKSIZE, compression='bz2' ) as df_reader:
            for chunk in df_reader:
                t1=time.time()
                quotations_with_mentions = chunk[chunk.quotation.str.contains(pattern)]
                quotations_with_mentions.to_json(path_or_buf=bzout_mention_usa,orient='records',lines=True)
                mentions = len(quotations_with_mentions)
                total_mentions += mentions
                t2=time.time()
                dt=t2-t1
                total_time+=dt
                chunk_number += 1
                if verbose:
                    # print(chunk_number)
                    print("Dumped {} political quotations containing mentions of other politicians out of {} quotations [quotations/s: {:.2f}]".format(mentions, CHUNKSIZE, CHUNKSIZE / dt))
def parse_mentions(QUOTE_MENTIONS, pattern, names_us_flat, QUOTE_PARSED_FLAT, QUOTE_PARSED_EXPLODED, verbose = False, US = False):
    try:
        os.remove(QUOTE_PARSED_FLAT)
        os.remove(QUOTE_PARSED_EXPLODED)
    except:
        pass
    CHUNKSIZE = 10000
    total_time,chunk_number=0,0
    with bz2.open(QUOTE_PARSED_FLAT, 'wb') as bzout_flat:
        with bz2.open(QUOTE_PARSED_EXPLODED, 'wb') as bzout_exploded:
            with pd.read_json(QUOTE_MENTIONS, lines=True, compression='bz2', chunksize = CHUNKSIZE) as df_reader:
                for chunk in df_reader:
                    t1=time.time()
                    chunk['qids']=chunk['qids'].apply(lambda x: x[0])
                    matches = chunk['quotation'].str.extractall(fr'({pattern})').reset_index().drop('match',axis=1).set_axis(['index','aliases'],axis='columns')
                    aliases = pd.merge(chunk,matches,how='left',left_index=True,right_on='index',sort=False)[['quoteID','aliases']].dropna()
                    aliases = aliases.drop_duplicates(subset=['quoteID','aliases'],keep='first')
                    if US:
                        mentions = pd.merge(aliases,names_us_flat,how='left',left_on='aliases',right_on='aliases_all',sort=False)[['quoteID','qid','name']].dropna()
                        mentions = mentions.drop_duplicates(subset=['quoteID','qid','name'],keep='first')
                    else:
                        mentions = pd.merge(aliases,names_us_flat,how='left',left_on='aliases',right_on='aliases_all',sort=False)[['quoteID','qid','name','country']].dropna()
                        mentions = mentions.drop_duplicates(subset=['quoteID','qid','name','country'],keep='first')
                    urls = chunk.explode('urls')
                    urls['urls']=urls['urls'].apply(lambda x: urlparse(x).netloc)
                    urls = urls[['quoteID','urls']]
                    urls= urls.drop_duplicates(subset=['quoteID','urls'],keep='first')
                    ResultSet_multrows = pd.merge(chunk,mentions,how='inner',on='quoteID',sort=False)
                    del ResultSet_multrows['urls']
                    del ResultSet_multrows['probas']
                    ResultSet_multrows = pd.merge(ResultSet_multrows,urls,how='inner',on='quoteID',sort=False)
                    ResultSet_multrows.rename(columns={'qid':'mentions_qids','name':'mentions'},inplace=True)
                    ResultSet_multrows['mentions_qids']=ResultSet_multrows['mentions_qids'].apply(lambda x:list(x.split(',')))
                    ResultSet_multrows['mentions']=ResultSet_multrows['mentions'].apply(lambda x:list(x.split(',')))
                    ResultSet_multrows['urls']=ResultSet_multrows['urls'].apply(lambda x:list(x.split(',')))
                    if not US:
                        ResultSet_multrows['country']=ResultSet_multrows['country'].apply(lambda x:list(x.split(',')))
                    pd3=mentions.groupby('quoteID')['name'].agg(list).reset_index()
                    pd4=mentions.groupby('quoteID')['qid'].agg(list).reset_index()
                    pd5=urls.groupby('quoteID')['urls'].agg(list).reset_index()
                    if not US:
                        pd6=mentions.groupby('quoteID')['country'].agg(list).reset_index()
                    ResultSet_singlerow = pd.merge(chunk,pd3,how='inner',on='quoteID',sort=False)
                    del ResultSet_singlerow['urls']
                    del ResultSet_singlerow['probas']
                    ResultSet_singlerow = pd.merge(ResultSet_singlerow,pd4,how='inner',on='quoteID',sort=False)
                    ResultSet_singlerow = pd.merge(ResultSet_singlerow,pd5,how='inner',on='quoteID',sort=False)
                    if not US:
                        ResultSet_singlerow = pd.merge(ResultSet_singlerow,pd6,how='inner',on='quoteID',sort=False)
                    ResultSet_singlerow.rename(columns={'qid':'mentions_qids','name':'mentions'},inplace=True)
                    ResultSet_singlerow.to_json(path_or_buf=bzout_flat,orient='records',lines=True)
                    ResultSet_multrows.to_json(path_or_buf=bzout_exploded,orient='records',lines=True)
                    t2=time.time()
                    dt=t2-t1
                    total_time+=dt
                    chunk_number += 1
                    if verbose:
                        print("Mapped {} US political mentionings to the mentioned politicians.  [quotations/s: {:.2f}]".format(chunk_number*CHUNKSIZE, CHUNKSIZE / dt))
# politician_df=pd.read_json(WIKI_DATA_FILTERED_LABELED, lines=True)
# politician_us_df = politician_df[politician_df['nationality']=='Q30'] #extract US politicians
# names_us=politician_us_df[['qid','name','aliases']] #extract qid, name, aliases
# names_us['aliases_all'] = [a+[b] for a,b in zip(names_us['aliases'],names_us['name'])]
# names_us_flat = names_us.explode('aliases_all')
# pattern = '|'.join(names_us_flat['aliases_all'].tolist())
# pattern = pattern.replace("(", "").replace(")", "")
