#Resources:
    #https://stackoverflow.com/questions/32759712/how-to-find-the-closest-word-to-a-vector-using-word2vec

#required python libraries
#pip install gensim
#pip install numpy

import re
from re import sub
import numpy as np
import gensim, sys
from gensim.models import Word2Vec
from numpy import add, subtract

class ProcessWordVectors:
    def __init__(self, model):
        self.model = Word2Vec.load(model)
        self.word_vecs   = self.model.wv

    def getWordVector(self, word):
        return self.word_vecs[word]

    def getSimilarity(self, word1, word2):
        return self.word_vecs.similarity(word1, word2)

    def mostSimilarWords(self, word, topn=5):
        return self.word_vecs.most_similar(word, topn=topn)

    def mostSimilarWordsFromVector(self, vector, topN = 10):
        return self.word_vecs.most_similar(positive=[vector], topn=topN)

    def leastSimilarWords(self, word, topn=5):
        return list(reversed(self.word_vecs.most_similar(word, topn=sys.maxsize)))[:topn]

    def vectorDifference(self, word1, word2):
        v1 = self.getWordVector(word1)
        v2 = self.getWordVector(word2)

        return self.mostSimilarWords(subtract(v1, v2))[2][0]

    def vectorAddition(self, word1, word2):
        v1 = self.getWordVector(word1)
        v2 = self.getWordVector(word2)

        return self.mostSimilarWords(add(v1, v2))[2][0]

global processer
processer = ProcessWordVectors("word2vec.model2")

equationDict    = {
    "+": np.add,
    "-": np.subtract,
    "*": np.multiply,
    "/": np.divide,
}

equationsString = r'[+\-*/]'

#Returns the resulting vector from an equation specified by a string
def returnVectorFromStringEquation(wordsList, equationsList):
    vectorReturn    = processer.getWordVector(wordsList[0])
    if (len(equationsList) > 0):
        for x in range(1, len(wordsList)):
            vectorReturn    = equationDict[equationsList[x - 1]](vectorReturn, processer.getWordVector(wordsList[x]))
    return vectorReturn

#Turns user input into a word list that can be processed by other functions
def processUserInput(stringEntered: str):
    wordList = re.split(equationsString, stringEntered)
    for x in range(len(wordList)):
        wordList[x] = wordList[x].strip()
    return wordList

#Formats the returned data and prints it neatly
def printWordList(wordsList, filterList):
    for wordSet in wordsList:
        (wordString, numMatch)  = wordSet
        if (wordString in filterList):
            continue
        numMatch    = np.floor(numMatch*100)
        print((wordString, f'{numMatch}%'))

#Handles user inputs and user prompts
def startProcesses():
    global isProcessing;
    stringEntered: str  = "a";
    while (stringEntered):
        stringEntered   = input("Enter your equation (i.e function + argument), ENTER NOTHING TO EXIT...\n")
        if (stringEntered):
            wordList    = processUserInput(stringEntered)
            print("");
            printWordList(processer.mostSimilarWordsFromVector(returnVectorFromStringEquation(wordList, re.findall(equationsString, stringEntered))), wordList)
            print("")

#WORKSPACE

