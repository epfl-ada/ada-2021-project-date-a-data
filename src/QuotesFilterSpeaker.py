import json
import bz2
import sys
import os
import pandas as pd
import time

# WIKI_DATA_FILTERED = 'filtered_politician.json.bz2'
# QUOTEBANK_POLITICIANS_WORLD= 'quotebank_politicians_world.json.bz2'
# QUOTEBANK_POLITICIANS_USA= 'quotebank_politicians_USA.json.bz2'
#quotebank_dir ='../data/'


def quotes_filter_speaker(quotebank_dir,QUOTEBANK_POLITICIANS_USA,WIKI_DATA_FILTERED,verbose):
    qids_df=pd.read_json(WIKI_DATA_FILTERED, lines=True)
    qids_us_df = qids_df[qids_df['nationality']=='Q30']
    # qid_list = list(qids_df.qid)
    qid_list_us = list(qids_us_df.qid)
    quotebank_files=list( os.path.join(quotebank_dir,x) for x in os.listdir(quotebank_dir))

    CHUNKSIZE = 100000
    try:
        # os.remove(QUOTEBANK_POLITICIANS_WORLD)
        os.remove(QUOTEBANK_POLITICIANS_USA)
    except:
        pass
    total_time, sum_quotes_world, sum_quotes_usa, chunk_number=0,0,0,0

    with bz2.open(QUOTEBANK_POLITICIANS_USA, 'wb') as bzout_usa:
        for file in quotebank_files:
            with pd.read_json(file, lines=True, compression='bz2', chunksize=CHUNKSIZE) as df_reader:
                for chunk in df_reader:
                    t1=time.time()
                    chunk_not_empty = chunk['qids'].apply(lambda x: len(x)) != 0
                    # chunk_politician = chunk[chunk_not_empty]['qids'].apply(lambda x: x[0]).isin(qid_list)
                    chunk_politician_us = chunk[chunk_not_empty]['qids'].apply(lambda x: x[0]).isin(qid_list_us)
                    # quote_world = chunk[chunk_not_empty & chunk_politician]
                    quote_usa = chunk[chunk_not_empty & chunk_politician_us]
                    # quote_world.to_json(path_or_buf=bzout_world,orient='records',lines=True)
                    quote_usa.to_json(path_or_buf=bzout_usa,orient='records',lines=True)
                    # sum_quotes_world += len(quote_world)
                    sum_quotes_usa += len(quote_usa)
                    t2=time.time()
                    dt=t2-t1
                    total_time += dt
                    chunk_number += 1
                    if verbose:
                        # print("Dumped {} political quotations and {} US political quotations among {} quotations [quotations/s: {:.2f}]".format(len(quote_world), len(quote_usa), chunk_number*CHUNKSIZE, sum_quotes_world / dt))
                        print("Dumped {} US political quotations among {} quotations [quotations/s: {:.2f}]".format( len(quote_usa), chunk_number*CHUNKSIZE, sum_quotes_world / dt))
                    