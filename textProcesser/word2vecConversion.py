#required python libraries
#pip install gensim
#pip install nltk

#code sourced from
#https://www.geeksforgeeks.org/python-word-embedding-using-word2vec/

import gensim
import os.path
from gensim.models import Word2Vec
from gensim.models import Phrases

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

import warnings

parentDirectory = os.path.dirname(__file__) + "/../C++ Corpora/"

FILE_ENDING: str    = ".txt"

MIN_WORD_COUNT: int = 15

WINDOW_SIZE: int    = 50

EPOCHS: int         = 30

CORPORA_FILES   = {
    parentDirectory + "WORD2VEC/" : [
        "allLemmatized"
    ],
}

def checkValidBigram(word: str):
    if (word.find("_") > 0):
        splitString = word.split("_")
        return (splitString[0].isalpha() and splitString[1].isalpha())
    return False

def processCorpus(corpusPath):
    text = ""
    with open(corpusPath, encoding='utf8') as file:
        text = file.read()
        file.close()

    text = text.replace("\n", " ") #replace new lines with spaces

    data = []
    for sentence in sent_tokenize(text): #split the text into sentences then iterate through them
        temp = []
        # tokenize the sentence into words
        for word in word_tokenize(sentence):
            word = word.lower().strip();
            if ((word.isalpha() and len(word) > 1) or checkValidBigram(word)):
                temp.append(word)
        data.append(temp)
    return data

def generateWordVectors():
    model = None
    for directory, fileList in CORPORA_FILES.items():
        for fileName in fileList:
            if (not model):
                model = gensim.models.Word2Vec(processCorpus(directory+fileName+FILE_ENDING), min_count = MIN_WORD_COUNT, vector_size = 300, window = WINDOW_SIZE)
                continue
            model.train(processCorpus(directory+fileName+FILE_ENDING), total_examples=1, epochs=EPOCHS)
    model.save("word2vec.model2")

generateWordVectors()
