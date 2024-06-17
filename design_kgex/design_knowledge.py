"""
Module for extracting design knowledge from a list of sentences.

Author: L. Siddharth,
Copyright: Data-Driven Innovation Lab, Singapore University of Technology and Design,
Email: siddharthl.iitrpr.sutd@gmail.com

"""

import warnings
warnings.filterwarnings("ignore")

from design_kgex.patent_text import cleanSentence
import torch

import requests
from bs4 import BeautifulSoup

import shutil
from tqdm import tqdm
from tqdm.auto import tqdm

from itertools import product

import os
import sys
import patoolib

import spacy
nlp = spacy.load('en_core_web_trf')
models = {
    "entity_relation_tagger": {
        "URL": "https://www.mediafire.com/file/ok1cfnf118uk2qk/entity_relation_tagger.rar/file", 
        "filename": "entity_relation_tagger.rar"
    },
    "relation_identifier": {
        "URL": "https://www.mediafire.com/file/5db8vot89tf5e7w/relation_identifier.rar/file",
        "filename": "relation_identifier.rar"
    }
}
def downloadModel(model):
    URL = models[model]["URL"]
    file_name = models[model]["filename"]
    download_page = requests.get(URL)
    soup = BeautifulSoup(download_page.content, 'html.parser')
    for item in soup.find(class_="download_link").find_all("a", href=True):
        if file_name in item['href']:
            with requests.get(item['href'], stream=True) as r:
                print(f"Downloading {file_name}...")
                total_length = int(r.headers.get("Content-Length"))
                with tqdm.wrapattr(r.raw, "read", total=total_length, desc="") as raw:
                    with open(os.path.basename(r.url), 'wb') as output:
                        shutil.copyfileobj(raw, output)
                patoolib.extract_archive(file_name, outdir = "design_kgex")
                os.remove(file_name)


def checkModelStatus(model):
    if model not in os.listdir("design_kgex"):
        downloadModel(model)
    return f"design_kgex/{model}"

token_identifier = spacy.load(checkModelStatus("entity_relation_tagger"))
relation_tagger = spacy.load(checkModelStatus("relation_identifier"))

def extractDesignKnowledge(sentences):
    if type(sentences) != list:
        if type(sentences) == str:
            sentences = [sentences]
            return returnFacts(sentences)
        else:
            return "Sorry! Please check the type of input. Type 'list' is required."
    else:
        return returnFacts(sentences)

def returnFacts(sentences):
    knowledge = []
    if torch.cuda.is_available():
        print("Congratulations, spaCy will now use GPU for processing!")
        spacy.prefer_gpu()
    else:
        print(f"Sorry, no GPU is available! Processing will be performed in normal time.")

    for sent in tqdm(sentences):
        knowledge.append(processSentence(cleanSentence(sent)))
        
    return knowledge

def pairEntities(head, tail, doc):
    text = list(doc.text)
    head_start, head_end = head[0].idx, head[-1].idx + len(head[-1].text)
    tail_start, tail_end = tail[0].idx, tail[-1].idx + len(tail[-1].text)

    if head_start < tail_start:
        text[head_start: head_end] = list("{HEAD ~ ") + text[head_start: head_end] + list("}")
        text[tail_start + 9: tail_end + 9] = list("{TAIL ~ ") + text[tail_start + 9: tail_end + 9] + list("}")
    else:
        text[tail_start: tail_end] = list("{TAIL ~ ") + text[tail_start: tail_end] + list("}")
        text[head_start + 9: head_end + 9] = list("{HEAD ~ ") + text[head_start + 9: head_end + 9] + list("}")

    return "".join(text)

def processSentence(sentence):
    doc = nlp(sentence)
    tags = [token.tag_ for token in token_identifier(doc.text)]
    entities = [chunk for chunk in doc.noun_chunks if (tags[chunk.root.i] == "ENT") & ("claim" not in chunk.text)]
    facts = []
    for (head, tail) in product(entities, entities):
        if (head.root.i < tail.root.i) & (head.text != tail.text):
            pairwise = relation_tagger(pairEntities(head, tail, doc))
            relations = [(token.text) for token in pairwise if token.tag_ == "REL"]
            if len(relations) > 0:
                if relations in [["of"], ["via"]]:
                    if head.end + 1 == tail.start:
                        facts.append([head.text, " ".join(relations), tail.text])
                else:
                    facts.append([head.text.lower(), " ".join(relations).lower(), tail.text.lower()])
    
    output = {"sentence": sentence,
              "entities": list(set([ent.text.lower() for ent in entities])),
              "facts": facts}
    
    return output