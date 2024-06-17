"""
Module for scraping patent text as a list of sentences upon providing patent number.

Author: L. Siddharth,
Copyright: Data-Driven Innovation Lab, Singapore University of Technology and Design,
Email: siddharthl.iitrpr.sutd@gmail.com

"""
import warnings
warnings.filterwarnings("ignore")

from bs4 import BeautifulSoup
import requests

import string
import re
import pickle
import os
import sys

import spacy
nlp = spacy.load('en_core_web_sm')

with open(os.path.join("design_kgex", "supplementary.pkl"), "rb") as f:
    supplementary = pickle.load(f)

roman, replaceables, headings = supplementary["roman"], supplementary["replaceables"], supplementary["headings"]

def cleanSentence(sentence):
    sentence = removeSequenceNumber(sentence)
    sentence = re.sub(r'\<[^<>}]*\>', '', re.sub(r'\{[^\{\}]*\}', '', re.sub(r'\[[^\[\]]*\]', '', re.sub(r'\([^()]*\)', '', str.replace(str.replace(sentence, "-", " "), "_", " ")))))
    sentence = re.sub(r'\<[^<>}]*\>', '', re.sub(r'\{[^\{\}]*\}', '', re.sub(r'\[[^\[\]]*\]', '', re.sub(r'\([^()]*\)', '', str.replace(str.replace(sentence, "-", " "), "_", " ")))))
    sentence = re.sub(r'\<[^<>}]*\>', '', re.sub(r'\{[^\{\}]*\}', '', re.sub(r'\[[^\[\]]*\]', '', re.sub(r'\([^()]*\)', '', str.replace(str.replace(sentence, "-", " "), "_", " ")))))

    sentence = sentence.replace("\"", "").replace("\"", "").replace("'", "").replace("'", "")

    while "  " in sentence:
        sentence = str.replace(sentence, "  ", " ")

    sentence = re.sub(r'\A\s', "", sentence)

    for key in replaceables:
        sentence = str.replace(sentence, key, replaceables[key])

    sentence = processClaims(sentence)
    return sentence


def processClaims(fullClaim):
    claimLines = [re.sub(r'\A\s', "", re.compile(re.escape('claim'), re.IGNORECASE).sub('claim', claimLine)) for claimLine in fullClaim.split("\n") if claimLine]
    processedLines = [removeClaimPhrases(claimLine) for claimLine in claimLines if removeClaimPhrases(claimLine)]

    return "\n\n".join(processedLines)


def removeClaimPhrases(claimLine):
    sentence = claimLine
    if sentence.split("*****")[0] == "DEP":
        if len(sentence.split("*****")) == 2:
            sentence = removeSequenceNumber(sentence.split("*****")[1])
            doc = nlp(sentence)
            endList = [{"name": chunk.text, "index": chunk.end-1} for chunk in doc.noun_chunks]
            tokenIndices = [{"name": tok.text, "index": tok.idx + len(tok.text) + 1} for tok in doc]
            for i in reversed(range(0, len(endList))):
                if "claim" in endList[i]["name"]:
                    sentence = sentence[: tokenIndices[endList[i-1]["index"]]["index"]] + sentence[tokenIndices[endList[i]["index"]]["index"]:]
    else:
        sentence = removeSequenceNumber(sentence)

    return sentence


def removeSequenceNumber(claimLine):
    sequenceNumber = claimLine.split(".")[0]
    if sequenceNumber.isnumeric():
        claimLine = claimLine.replace(sequenceNumber + ". ", "")
    if sequenceNumber in list(string.ascii_lowercase):
        claimLine = claimLine.replace(sequenceNumber + ". ", "")
    if sequenceNumber in roman:
        claimLine = claimLine.replace(sequenceNumber + ". ", "")

    return claimLine


def processScrapedData(scrapedData, patent_headings):
    for key in patent_headings:
        if key not in headings:
            scrapedData.pop(key, None)

    sentences = []
    for key in scrapedData:
        for sentence in scrapedData[key]:
            processed = cleanSentence(sentence)
            for txt in processed.split("\n"):
                doc = nlp(txt)
                for sent in doc.sents:
                    if len(nlp(sent.text)) in range(15, 100):
                        sentences.append(sent.text)
    return sentences


def getPatentText(patent_id):
    URL = f"https://patents.google.com/patent/US{patent_id}"
    patentPage = requests.get(URL)
    if patentPage:
        soup = BeautifulSoup(patentPage.content, 'html.parser')
        output = {}
        currentHead = "NIL"
        output[currentHead] = []
        if soup:
            mainBody = soup.find(class_="description")
            if mainBody:
                descriptionItems = mainBody.find_all(["heading", "div"])
                for item in descriptionItems:
                    if item.name == "heading":
                        currentHead = item.get_text()
                        output[currentHead] = []
                    else:
                        output[currentHead].append(item.get_text())

            claimsSection = soup.find(class_="claims")
            if claimsSection:
                individualClaims = claimsSection.find_all(class_="claim")
                claims = []
                for item in individualClaims:
                    claims.append(item.get_text())
                output["CLAIM"] = claims

            abstractSection = soup.find(class_="abstract")
            if abstractSection:
                output["ABSTRACT"] = [abstractSection.get_text()]
        else:
            print("Please enter a valid Patent ID!")
        patent_headings = list(output.keys())
    else:
        print("Please enter a valid patent number")

    sentences = processScrapedData(output, patent_headings)
    
    return sentences
