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

def processWord(word):
    tempWord = ""
    for letter in word:#break the word into letters then check if its a valid character
        if letter.isalpha():
            tempWord += letter
        elif letter == "_":
            tempWord += letter
    return tempWord

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
            tempWord = processWord(word)
            if not tempWord == '':#if the word isnt entirely blank after checking if each character is valid then add it to the words list
                temp.append(tempWord.lower())
        data.append(temp)
    return data

def generateWordVectors():
    data1 = processCorpus("../C++ Corpora/Processed/CPP_Corpus_LARGE.txt")
    data2 = processCorpus("../C++ Corpora/Processed/CPP_Corpus_MEDIUM.txt")
    data3 = processCorpus("../C++ Corpora/Processed/CPP_Corpus_SMALL.txt")
    data4 = processCorpus("../C++ Corpora/Processed/CPP_Corpus_MEDIUM2.txt")
    model = gensim.models.Word2Vec(data1, min_count = 10, vector_size = 300, window = 5)
    model.train(data2, total_examples=1, epochs=1)
    model.train(data3, total_examples=1, epochs=1)
    model.train(data4, total_examples=1, epochs=1)
    model.save("word2vec.model")

generateWordVectors()
