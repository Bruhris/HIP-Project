#required python libraries
#pip install gensim
#pip install nltk

#code sourced from
#https://www.geeksforgeeks.org/python-word-embedding-using-word2vec/

import gensim
from gensim.models import Word2Vec
from gensim.models import Phrases

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
nltk.download('punkt')
nltk.download('stopwords')

import warnings

# def checkValidBigram(word: str):
#     if (word.find("_") > 0):
#         splitString = word.split("_")
#         return (splitString[0].isalpha() and splitString[1].isalpha())
#     return False

def processCorpus(corpusPath):
    text = ""

    with open(corpusPath, encoding='utf8') as file:
        text = file.read()
        file.close()

    text = text.replace("\n", " ")

    data = []

    for sentence in sent_tokenize(text): #split the text into sentences then iterate through them
        temp = []
        # tokenize the sentence into words
        for word in word_tokenize(sentence):
            tempWord = ""
            for letter in word:
                if letter.isalpha():
                    tempWord += letter
                elif letter == "_":
                    tempWord += letter
            if not tempWord == '':
                temp.append(tempWord.lower())

        data.append(temp)

    bigram_detector = Phrases(data)
    data = bigram_detector[data]

    return data

def generateWordVectors():
    beginning   = "../textNormalizer/processed/sentence_only/lemmatized"
    ending      = ".txt"
    textFiles   = [
        "CORPUS_GIT",
        "CORPUS_OREILLY",
        "CPP_Corpus_LARGE_PURE",
        "CPP_Corpus_MEDIUM2_PURE",
        "CPP_Corpus_SMALL_PURE"
    ]

    model = gensim.models.Word2Vec(processCorpus("../../mengyan4_text_normalizer/processed/sentence_only/allLemmatized.txt"), min_count = 10, vector_size = 300, window = 5)
    model.save("word2vec.model")

generateWordVectors()
