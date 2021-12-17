import os, re, time, bz2
from urllib.parse import urlparse
import pandas as pd
import numpy as np

BIAS_DATA = "../data/bias_scores.csv"
bias_df = pd.read_csv(BIAS_DATA)


def get_bias_score(urls):
    """
    pass in a list urls return the mean media bias score
    or nan if none if the urls is included in the media bias
    database
    """
    scores = []

    # get path of the url
    urls = [urlparse(u).path for u in urls]
    # remove www if there is
    www_re = re.compile(r"(www\.)?")
    urls = [www_re.sub("", u) for u in urls]
    for u in urls:
        # takes the mean of the matched results
        ss = bias_df[bias_df["domain"].str.match(u)]["score"]
        if not ss.empty:
            scores.append(ss.mean())

    if scores:
        return np.nanmean(scores)
    else:
        return np.nan


def save_bias(save_file, read_file, chunksize=3000):
    """append bias score to read_file and save to save_file in chunks"""
    try:
        os.remove(save_file)
    except:
        pass

    total_time, total_mentions, chunk_number = 0, 0, 0
    mentions = []

    with bz2.open(save_file, "wb") as bz_writer:
        with pd.read_json(
            read_file, lines=True, chunksize=chunksize, compression="bz2"
        ) as df_reader:
            for chunk in df_reader:
                t1 = time.time()

                # get bias
                bias = [get_bias_score(urls) for urls in chunk["urls"]]
                chunk["source_bias"] = bias

                chunk.to_json(
                    path_or_buf=bz_writer, orient="records", lines=True
                )
                mentions = len(chunk)
                total_mentions += mentions
                t2 = time.time()
                dt = t2 - t1
                total_time += dt
                chunk_number += 1
                print(
                    "Dumped {} quotations out of {} quotations [quotations/s: {:.2f}]".format(
                        mentions, chunksize, chunksize / dt
                    )
                )
