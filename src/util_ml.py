import pandas as pd
from typing import Protocol
from gensim.utils import pickle
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from gensim.corpora.dictionary import Dictionary
from gensim.models import LdaModel
import spacy

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
dictionary = Dictionary.load(model_path + ".id2word")
lda_model = LdaModel.load(model_path)

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


if __name__ == "__main__":
    pass
