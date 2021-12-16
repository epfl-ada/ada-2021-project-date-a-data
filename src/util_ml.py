import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from gensim.corpora.dictionary import Dictionary
from gensim.models import LdaModel
import bz2
import time
import spacy
import os
import numpy as np
from nltk.corpus import PlaintextCorpusReader
from gensim.models import LdaMulticore

# nlp pipeline
nlp = spacy.load("en_core_web_sm")
# customize pipeline
# lemmatizer: reduce words to basic form, eg. talking -> talk, president -> presid
nlp.remove_pipe("lemmatizer")
# tagger: tag the part of speech for the token i.e. noun, verb, etc
nlp.remove_pipe("tagger")
STOPWORDS = spacy.lang.en.stop_words.STOP_WORDS

# load LDA model
model_path = "../model/lda_bow"
try:
    dictionary = Dictionary.load(model_path + ".id2word")
    lda_model = LdaModel.load(model_path)
except FileNotFoundError:
    print("Model file not found, please run util_ml.py as script.")

# read pol_name_global for preprocessing
POLITICIAN = "../data/filtered_politician_labeled_v3.json.bz2"
pol_df = pd.read_json(POLITICIAN, lines=True, compression="bz2")

# extend names with aliases
pol_df["aliases_all"] = [
    a + [b] for a, b in zip(pol_df["aliases"], pol_df["name"])
]
pol_name_global = pol_df["aliases_all"].tolist()
pol_name_global = frozenset([n for names in pol_name_global for n in names])


def get_sentiment(docs):
    """
    return sentiment scores of input docs
    use nltk.vader.sentiment analysis pretrained model
    """
    sid = SentimentIntensityAnalyzer()
    return [sid.polarity_scores(s)["compound"] for s in docs]


def predict_LDA(docs):
    """
    return topic index and probability using trained
    LDA model
    """

    processed_docs = preprocess_nlp(docs)
    topic_index, topic_scores = domiant_topic(
        processed_docs, lda_model, dictionary
    )
    return topic_index, topic_scores


def preprocess_nlp(docs, n_process=4, batch_size=10):
    """get processed corpus by nlp pipeline while removing names"""

    processed_docs = []
    for doc in nlp.pipe(docs, n_process=n_process, batch_size=batch_size):
        # Process document using Spacy NLP pipeline.
        ents = doc.ents  # Named entities

        # Keep only words (no numbers, no punctuation).
        # if remove lemmentizer in nlp pipe, what happens here?
        # convert token to string while remove punctuation and stopwords
        doc = [
            token.text for token in doc if token.is_alpha and not token.is_stop
        ]
        # print(doc)
        # Remove common words from a stopword list and keep only words of length 3 or more.
        doc = [
            token for token in doc if token not in STOPWORDS and len(token) > 2
        ]

        # Add named entities, but only if they are a compound of more than word.
        doc.extend([str(entity) for entity in ents if len(entity) > 1])

        # remove names, have to put after adding entities
        doc = [
            token
            for token in doc
            if token not in pol_name_global and len(token) > 2
        ]

        processed_docs.append(doc)
    return processed_docs


def domiant_topic(processed_docs, lda_model, dictionary):
    """get the most probable topic for given doc"""
    bow_vectors = [dictionary.doc2bow(text) for text in processed_docs]

    topic_idx = []
    topic_score = []
    for row in lda_model[bow_vectors]:
        row = sorted(row, key=lambda x: x[1], reverse=True)
        topic_idx.append(row[0][0])
        topic_score.append(row[0][1])
    return topic_idx, topic_score


def save_sentiment_topics(save_file, read_file, chunk_size=5000):
    """add sentiment score, topic index, and topic probability to data file"""
    try:
        os.remove(save_file)
    except:
        pass

    total_time, total_mentions, chunk_number = 0, 0, 0
    mentions = []
    sid = SentimentIntensityAnalyzer()

    with bz2.open(save_file, "wb") as bz_writer:
        with pd.read_json(
            read_file, lines=True, chunksize=chunk_size, compression="bz2"
        ) as df_reader:
            for chunk in df_reader:
                t1 = time.time()

                docs = chunk["quotation"].to_list()
                # LDA topic
                processed_docs = preprocess_nlp(docs)
                topic_index, topic_scores = domiant_topic(
                    processed_docs, lda_model, dictionary
                )
                chunk["topic_index"] = topic_index
                chunk["topic_scores"] = topic_scores

                # sentiment analysis
                sentiment_score = get_sentiment(docs)
                chunk["sentiment"] = sentiment_score

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
                        mentions, chunk_size, chunk_size / dt
                    )
                )


def get_chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i : i + n]


if __name__ == "__main__":
    # import all quotations data of US
    print(">>> running as script, begin to prepare LDA model")
    print(">>> loading US quotations data")
    USA_DATA = "../data/quotes_mentions_USA_compact.json.bz2"
    df = pd.read_json(USA_DATA, lines=True, compression="bz2")

    # convert quotations to corpus by year
    corpus_root = "../data"
    for year in range(2015, 2021):
        file_path = "../data/quotations_{:d}.txt".format(year)
        df_year = df[
            (df["date"] >= pd.Timestamp(year, 1, 1))
            & (df["date"] < pd.Timestamp(year + 1, 1, 1))
        ]
        quotations = "\n".join(df_year["quotation"].to_list())
        print("number of chars {} in year {}".format(len(quotations), year))

        with open(file_path, "w") as f:
            f.write(quotations)

    print(">>> convert to corpus and sample quotations by year")
    # read quotations as corpus
    corpus_root = "../data"
    quotations_corpus = PlaintextCorpusReader(corpus_root, "quotations.*.txt")

    # Get the chunks, otherwise too large to handle
    corpus_id = {
        f: n for n, f in enumerate(quotations_corpus.fileids())
    }  # dictionary of books
    chunks = list()
    chunk_class = (
        list()
    )  # this list contains the original book of the chunk, for evaluation

    limit = 60  # how many chunks total for one corpus
    size = 100  # how many sentences per chunk/page

    for f in quotations_corpus.fileids():
        sentences = quotations_corpus.sents(f)
        print(f)
        print("Number of sentences:", len(sentences))

        # create chunks
        chunks_of_sents = [
            x for x in get_chunks(sentences, size)
        ]  # this is a list of lists of sentences, which are a list of tokens
        chs = list()

        # regroup so to have a list of chunks which are strings
        for c in chunks_of_sents:
            grouped_chunk = list()
            for s in c:
                grouped_chunk.extend(s)
            chs.append(" ".join(grouped_chunk))
        print("Number of chunks:", len(chs), "\n")

        # filter to the limit, to have the same number of chunks per book
        chunks.extend(chs[:limit])
        chunk_class.extend([corpus_id[f] for _ in range(len(chs[:limit]))])

    print(">>> preprocessing data and generating bow")
    noname_docs = preprocess_nlp(chunks)
    dictionary = Dictionary(noname_docs)

    # Remove rare and common tokens.
    # Filter out words that occur too frequently or too rarely.
    max_freq = 0.4
    min_wordcount = 5
    dictionary.filter_extremes(no_below=min_wordcount, no_above=max_freq)

    # Bag-of-words representation of the documents.
    noname_corpus = [dictionary.doc2bow(doc) for doc in noname_docs]

    print("Number of unique tokens: %d" % len(dictionary))
    print("Number of chunks: %d" % len(noname_corpus))

    print(">>> training")

    seed = 1
    # random.seed(seed)
    np.random.seed(seed)

    params = {"passes": 10, "random_state": seed}
    base_models = dict()
    model_LDA_noname = LdaMulticore(
        corpus=noname_corpus,
        num_topics=10,
        id2word=dictionary,
        workers=6,
        passes=params["passes"],
        random_state=params["random_state"],
    )

    print(">>> saving model")
    model_folder = "../model/"
    model_prefix = "lda_bow"
    if not os.path.isdir(model_folder):
        os.mkdir(model_folder)
    model_LDA_noname.save(os.path.join(model_folder, model_prefix))

    print(">>> topics extracted")
    model_LDA_noname.show_topics(num_topics=10)
