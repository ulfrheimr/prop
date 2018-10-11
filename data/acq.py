#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
import sys

sys.path.append('../')
sys.path.append('../../text_utils')

import argparse
import collections
import ConfigParser
import nltk
import os
import requests
import time
import threading
from pdb import set_trace as bp

import cPickle as pickle

import text_utils
from text_utils import preprocessing
from text_utils import utils
from text_utils import indexing


P = utils.Pool
corpus = preprocessing.corpus
lock = threading.Lock()


def index_data(path, url):
    indexer = indexing.solr_post.SolrPost(url)

    docs = []
    files = [os.path.join(path, f) for f
             in os.listdir(path)
             if os.path.isfile(os.path.join(path, f))]

    for _file in files:
        if os.path.splitext(_file)[-1] != "":
            temp_corpus = corpus.unpickle_data(_file)
            docs += temp_corpus

    for doc in docs:
        print "Posting", doc["url"]

        tt = nltk.tokenize.TextTilingTokenizer()
        par_count = 1

        for page in doc["pages"]:
            page_text = page["page"]

            try:
                pars = tt.tokenize(page_text)
            except ValueError as e:
                pars = [page_text]
            except Exception as e:
                print e
                raise

            res_pars = []
            total_length = 0
            acc = ""
            for par in pars:
                acc += par
                if len(acc) > 600:
                    res_pars.append(acc)
                    acc = ""

            if acc != "":
                res_pars.append(acc)

            for par in res_pars:
                data = {
                    "content": par,
                    "doc_uri": doc["url"],
                    "page_uri": page["url"],
                    "ordinal": par_count,
                    "lang": "english"
                }

                indexer.post_text("proposal", data)

                par_count += 1


class DocumentCrawler(P):
    crawled = []
    already_crawled = set()
    batch_size = 50

    headers = {"Accept-Encoding": "gzip, deflate, br",
               "Content-Type": "application/json"}

    def __init__(self, dest_path, species_file, url, split_size = 10, threadNames=["t1"], onFinish=None):
        self.corpus_serial = 1
        self.corpus_id = os.path.splitext(species_file)[0]\
            .split("/").pop()
        self.count = 0
        self.dest_path = dest_path
        self.species_file = species_file
        self.url = url
        self.set_threads(threadNames)
        self.split_size = int(split_size)

    def read_species(self):
        species = {}
        all_species = set()
        othr_species = set()

        with open(self.species_file) as _f:
            lines = _f.readlines()

            for line in lines:
                line = line.replace("\n", "").lower()
                all_species.add(line)

                spp = line.split()
                sp = spp[0]

                if sp not in species:
                    species[sp] = []

                species[sp].append(line)

        return species, all_species

    def name_results(self, species):
        species = "\"" + species + "\""
        query = """
        {
        nameResults(name:""" + species + """){
            titles{
            	ItemUrl
              TitleInfo{
                lang
              }
              Pages{
            		PageUrl
            		OcrUrl
              }
            }
          }
        }
        """

        request = requests.post(self.url,
                                json={'query': query},
                                headers=self.headers)

        if request.status_code == 200:
            return request.json()["data"]
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(
                request.status_code, query))

    def names(self, species):
        species = "\"" + species + "\""
        query = """
        {
          names(name:""" + species + """)
        }
        """

        request = requests.post(self.url,
                                json={'query': query},
                                headers=self.headers)

        if request.status_code == 200:
            return request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(
                request.status_code, query))

    def get_document(self, id):
        query = """
        {
        title(id:""" + str(id) + """){
            ItemUrl
            Pages{
              PageUrl
              TextOCR{
                text
              }
            }
          }
        }
        """

        request = requests.post(self.url,
                                json={'query': query},
                                headers=self.headers)

        if request.status_code == 200:
            return request.json()
        else:
            raise Exception("Query failed to run by returning code of {}. {}".format(
                request.status_code, query))

    def get_documents(self):
        not_found = set()
        retrieved_docs = {}
        othr_species = set()

        species, all_species = self.read_species()

        for spp, spps in species.items():
            # First we get specific species
            for sp in spps:
                print "RETRIEVING", sp

                try:
                    titles = self.name_results(sp)
                    titles = titles["nameResults"]
                except Exception as e:
                    print e
                    continue

                if not titles:
                    not_found.add(sp)
                    continue

                titles = titles[0]["titles"]

                for t in titles:
                    id = t["ItemUrl"]
                    try:
                        lang = t["TitleInfo"]["lang"]
                        if lang.lower() != "english":
                            continue
                    except:
                        print "Can't retrieve info of ", id
                        continue

                    if id in retrieved_docs:
                        retrieved_docs[id]["species"].append(sp)
                    else:
                        retrieved_docs[id] = {
                            "info": t,
                            "species": [sp]
                        }

            related_species = self.names(spp)
            related_species = related_species["data"]["names"]

            for spp in related_species:
                sp = spp.lower()

                if sp not in species:
                    othr_species.add(sp)

        pickle_file = open(os.path.join(self.dest_path, "not_found.pkl"), 'ab')
        pickle.dump(not_found, pickle_file)

        pickle_file = open(os.path.join(self.dest_path, "othr.pkl"), 'ab')
        pickle.dump(othr_species, pickle_file)

        return retrieved_docs, species

    def setPool(self):
        count = 0
        previous_docs = {}
        docs_to_crawl = {}

        retrieved_docs, species = self.get_documents()

        try:
            data_file = open(os.path.join(
                self.dest_path, "crawled.pkl"), "rb")
            previous_docs = pickle.load(data_file)
        except IOError as e:
            print "NOT FOUND PREVIOUS CRAWLED SPECIES"
        except Exception as e:
            raise

        for doc in retrieved_docs.items():
            key = doc[0]

            if previous_docs.get(key, None) is None:
                # Check for update if species changes
                pass

            docs_to_crawl[key] = doc[1]

        num_found = len(docs_to_crawl.keys())

        batches = [{"start": r,
                    "total": num_found,
                    "docs": docs_to_crawl.items()[r:(r + 1) * self.batch_size]
                    }
                   for r in range(0, num_found, self.batch_size)]

        return batches

    def process(self, thread, **kwargs):
        start = kwargs["start"]
        total = kwargs["total"]
        docs = kwargs["docs"]

        crawled = []

        for key, doc in docs:
            id = key.split("/").pop()
            self.count += 1

            if key in self.already_crawled:
                continue

            try:
                try:
                    document = self.get_document(id)
                    document = document["data"]["title"]
                    pages = document["Pages"]
                except Exception as e:
                    print "Doc has no pages"
                    raise e

                ret_doc = {"url": document["ItemUrl"],
                           "pages": []
                           }

                num_page = 1
                for p in pages:
                    try:
                        page = p["TextOCR"]["text"]
                        ret_doc["pages"].append({"url": p["PageUrl"],
                                                 "page": page,
                                                 "num_page": num_page})
                        num_page += 1
                    except Exception as e:
                        print "Error getting page for doc", key

                print "AT", self.count, "of", total
                self.crawled.append([key, doc])

                with lock:
                    pickle_file = open(os.path.join(self.dest_path, "corpus_" +
                                                    self.corpus_id + "_" +
                                                    str(self.corpus_serial) + ".pkl"), 'ab')
                    pickle.dump(ret_doc, pickle_file)

                if self.count % self.split_size == 0:
                    print "SELF HEALING, PLEASE CHECK"
                    self.corpus_serial += 1
            except Exception as e:
                print "Error on " + key + "\n"
                continue

    def onFinish(self):
        with lock:
            pickle_file = open(os.path.join(
                self.dest_path, "crawled.pkl"), 'w')
            pickle.dump(self.crawled, pickle_file)
        print "CORPUS BUILT"


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
                             help="Path of the file to read all corpus paragraphs", metavar="FILE")
    conf_parser.add_argument("-sf", "--species_file",
                             help="Path of the file to read all corpus paragraphs", metavar="FILE")
    conf_parser.add_argument("-dp", "--dest_path",
                             help="Path of the file to read all corpus paragraphs", metavar="FILE")
    conf_parser.add_argument("-u", "--url",
                             help="Path of the file to read all corpus paragraphs", metavar="FILE")

    conf_parser.add_argument("-sp", "--split",
                             help="Path of the file to read all corpus paragraphs", metavar="FILE")

    args, remaining_argv = conf_parser.parse_known_args()

    DocumentCrawler(dest_path=args.dest_path,
                    species_file=args.species_file,
                    url=args.url,
                    split_size=args.sp).start()
