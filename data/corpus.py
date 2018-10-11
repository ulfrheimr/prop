#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import sys

sys.path.append('../../')
sys.path.append('../../text_utils')

import argparse
import collections
import ConfigParser
import os
import requests
import time
import threading

import cPickle as pickle

import text_utils
from text_utils import preprocessing
from text_utils import utils
from text_utils import indexing

from datetime import date
from pdb import set_trace as bp

Pool = utils.Pool
Post = indexing.solr_post.SolrPost


lock = threading.Lock()


class TopicTrainCorpus(Pool):
    batch_size = 100
    prev = ""
    terms = ["habitat",
             "archipelago",
             "spring",
             "water body",
             "mountain",
             "island",
             "riffle",
             "headwater",
             "isthmus",
             "moraine",
             "wave-cut",
             "platform",
             "meander",
             "harbor",
             "shoreline",
             "arrugado",
             "talik",
             "autotrophy",
             "heterotrophy",
             "coprophagy",
             "saprophagy",
             "predator",
             "producer",
             "consumer",
             "detritovore",
             "omnivore",
             "herbivore",
             "carnivore",
             "mesoamerica",
             "mexico",
             "michoacan",
             "canada",
             "costa rica",
             "alajuela",
             "perennial"
             ]
    found = set()

    def __init__(self, path, solr_url, solr_core, threadNames=["t1", "t2"], onFinish=None):
        self.current = 1
        self.path = path
        self.solr_url = solr_url
        self.solr_core = solr_core
        self.set_threads(threadNames)
        self.indexer = Post(solr_url)
        self.finishCallback = onFinish

    def setPool(self):
        all_batches = []
        for term in self.terms:
            results = self.indexer.select(
                self.solr_core, "q=open_search:\"" + term + "\"&fl=id")
            num_found = results["response"]["numFound"]

            batches = [{"start": r, "total": num_found, "term": term}
                       for r in range(0, num_found, self.batch_size)]
            all_batches += batches


        print "Total", len(all_batches)

        return all_batches

    def process(self, thread, **kwargs):
        write_docs = []
        start = kwargs["start"]
        num_found = kwargs["total"]
        term = kwargs["term"]

        if term != self.prev:
            print ""
            self.prev = term

        sys.stdout.write("AT  %d of %d with %s\r" % (start, num_found, term))
        sys.stdout.flush()

        query = "fl=id,open_search,page_uri&q=open_search:\"" + term + "\"" +\
            "&rows=" + str(self.batch_size) + "&start=" + str(start)

        results = self.indexer.select(self.solr_core, query)

        docs = results["response"]["docs"]
        for doc in docs:
            id = doc["id"]

            if id in self.found:
                print "REPEAT", id
                continue

            write_docs.append(doc)

        with lock:
            dest_file = os.path.join(
                self.path, "topic_train_corpus_" + date.today().strftime("%Y_%m_%d") + ".pkl")
            pickle_file = open(dest_file, 'ab')
            pickle.dump(write_docs, pickle_file)

    def onFinish(self):
        self.finishCallback()


class SpeciesTrainCorpus(Pool):
    batch_size = 50

    def __init__(self, path, solr_url, solr_core, threadNames=["t1", "t2"], onFinish=None):
        self.path = path
        self.solr_url = solr_url
        self.solr_core = solr_core
        Pool.threadNames = threadNames
        self.indexer = Post(solr_url)
        self.finishCallback = onFinish

    def setPool(self):
        results = self.indexer.select(self.solr_core, "q=species:*&fl=id")
        num_found = results["response"]["numFound"]

        batches = [{"start": r, "total": num_found}
                   for r in range(0, num_found, self.batch_size)]

        return batches

    def process(self, thread, **kwargs):
        start = kwargs["start"]
        num_found = kwargs["total"]
        sys.stdout.write("AT  %d of %d\r" % (start, num_found))
        sys.stdout.flush()

        query = "fl=id,species,page_uri&q=species:*&rows=" + \
            str(self.batch_size) + "&start=" + str(start)
        results = self.indexer.select(self.solr_core, query)

        docs = results["response"]["docs"]

        with lock:
            dest_file = os.path.join(self.path, "species_train_corpus.pkl")
            pickle_file = open(dest_file, 'ab')
            pickle.dump(docs, pickle_file)

    def onFinish(self):
        self.finishCallback()


def create_train_corpus(dest_path, solr_url, solr_core):
    def on_finish():
        print "END"

    ttc = TopicTrainCorpus(path=dest_path,
                           solr_url=solr_url,
                           solr_core=solr_core,
                           threadNames=["t1", "t2"],
                           onFinish=on_finish)
    ttc.start()

    # stc = SpeciesTrainCorpus(path=dest_path,
    #                          solr_url=solr_url,
    #                          solr_core=solr_core,
    #                          threadNames=["t1", "t2"],
    #                          onFinish=on_finish)
    #
    # stc.start()


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

    conf_parser.add_argument("-t", "--train",
                             help="Create train corpus", metavar="FILE")
    conf_parser.add_argument("-dp", "--dest_path",
                             help="Destination path of corpus", metavar="FILE")
    conf_parser.add_argument("-u", "--url",
                             help="Destination path of corpus", metavar="FILE")
    conf_parser.add_argument("-c", "--core",
                                 help="Destination path of corpus", metavar="FILE")

    args, remaining_argv = conf_parser.parse_known_args()

    # solr_url = "http://localhost:8985/solr/"
    # solr_core = "proposal"

    create_train_corpus(args.dest_path, args.url, args.core)
