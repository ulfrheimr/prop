#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

sys.path.append('../../')
sys.path.append('../../text_utils')

import argparse
import collections
import ConfigParser

import os
import re
import numpy as np
from pprint import pprint

# Gensim
import gensim
import gensim.corpora as corpora
from gensim.utils import simple_preprocess
from gensim.test.utils import datapath
from gensim.models import CoherenceModel

# spacy for lemmatization
import spacy

# Plotting tools
import pyLDAvis
import pyLDAvis.gensim  # don't skip this
import matplotlib.pyplot as plt

from nltk.corpus import stopwords
from pdb import set_trace as bp

import pydash
import text_utils
import unidecode
from text_utils import preprocessing

corpus = preprocessing.corpus
stop_words = stopwords.words('english')
stop_words.extend(['from', 'subject', 're', 'edu', 'use'])


def sent_to_words(sentences):
    for sentence in sentences:

        try:
            # deacc=True removes punctuations
            s = unidecode.unidecode(sentence)
            temp = gensim.utils.simple_preprocess(str(s), deacc=True)
            yield(temp)
        except Exception as e:
            raise


def remove_stopwords(texts):
    return [[word for word in simple_preprocess(str(doc)) if word not in stop_words] for doc in texts]


def make_bigrams(bigram_mod, texts):
    return [bigram_mod[doc] for doc in texts]


def make_trigrams(texts):
    return [trigram_mod[bigram_mod[doc]] for doc in texts]


def lemmatization(nlp, texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
    """https://spacy.io/api/annotation"""
    texts_out = []
    for sent in texts:
        doc = nlp(" ".join(sent))
        texts_out.append(
            [token.lemma_ for token in doc if token.pos_ in allowed_postags])
    return texts_out


def create_data_words(corpus_file):
    train_corpus = []
    train_corpus = corpus.unpickle_data(corpus_file)

    # Convert to list
    data = pydash.chain(train_corpus)\
        .flatten().map(lambda x: x["open_search"])\
        .value()

    del train_corpus

    # Corpus prepreocessing

    # Mail
    data = [re.sub('\S*@\S*\s?', '', sent) for sent in data]

    # Line chars
    data = [re.sub('\s+', ' ', sent) for sent in data]

    # Single quotes
    data = [re.sub("\'", "", sent) for sent in data]

    # using nltk
    data_words = list(sent_to_words(data))

    return data_words


def make(corpus_path, dest_path, num_topics=50, passes=10):
    corpus_id = corpus_path.split("/").pop().replace('.pkl', "")
    cfname = os.path.join(dest_path, "lda_" + corpus_id)
    data_words = create_data_words(corpus_path)

    bp()

    print "MAKING GRAM MODELS"
    # Build the bigram and trigram models
    # higher threshold fewer phrases.
    bigram = gensim.models.Phrases(data_words, min_count=5, threshold=100)
    trigram = gensim.models.Phrases(bigram[data_words], threshold=100)

    # Ngram models
    bigram_mod = gensim.models.phrases.Phraser(bigram)
    trigram_mod = gensim.models.phrases.Phraser(trigram)

    data_words_nostops = remove_stopwords(data_words)
    data_words_bigrams = make_bigrams(bigram_mod, data_words_nostops)

    # Initialize spacy 'en' model, keeping only tagger component (for efficiency)
    nlp = spacy.load('en', disable=['parser', 'ner'])

    # Do lemmatization keeping only noun, adj, vb, adv
    data_lemmatized = lemmatization(nlp,
                                    data_words_bigrams,
                                    allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])

    print "MAKING CORPUS RESOURCES"
    texts = data_lemmatized

    # Dictionary
    id2word = corpora.Dictionary(data_lemmatized)

    # TDF
    corpus = [id2word.doc2bow(text) for text in texts]

    lda_model = None

    # # Check if model exists
    if not os.path.isfile(cfname):
        # LDA model
        lda_model = gensim.models.ldamodel.LdaModel(corpus=corpus,
                                                    id2word=id2word,
                                                    num_topics=num_topics,
                                                    random_state=100,
                                                    update_every=1,
                                                    chunksize=100,
                                                    passes=passes,
                                                    alpha='auto',
                                                    per_word_topics=True)
        lda_model.save(cfname)
    else:
        print "MODEL FOUND USING PREVIOUS"
        lda_model = gensim.models.ldamodel.LdaModel.load(cfname)

    doc_lda = lda_model[corpus]

    # Compute Perplexity
    # a measure of how good the model is. lower the better.
    print('\nPerplexity: ', lda_model.log_perplexity(corpus))

    # Compute Coherence Score
    coherence_model_lda = CoherenceModel(
        model=lda_model, texts=data_lemmatized, dictionary=id2word, coherence='c_v')
    coherence_lda = coherence_model_lda.get_coherence()
    print('\nCoherence Score: ', coherence_lda)

    # Topics
    vis = pyLDAvis.gensim.prepare(lda_model, corpus, id2word, mds='mmds')
    vis_file_name = dest_path + '/' + \
        str(num_topics) + "_" + corpus_id + ".html"
    pyLDAvis.save_html(vis, vis_file_name)


if __name__ == "__main__":
    '''
    We use this to index all docs written with spanish chars
    '''
    reload(sys)
    sys.setdefaultencoding('ISO-8859-1')

    conf_parser = argparse.ArgumentParser(
        description=__doc__,  # printed with -h/--help
        # Don't mess with format of description
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # Turn off help, so we print all options in response to -h
        add_help=False
    )

    conf_parser.add_argument("-cp", "--corpus_path",
                             help="  ", metavar="FILE")
    conf_parser.add_argument("-dp", "--dest_path",
                             help="  ", metavar="FILE")

    args, remaining_argv = conf_parser.parse_known_args()
    make(args.corpus_path, args.dest_path)
