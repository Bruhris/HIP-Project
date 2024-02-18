#Resources:
    #https://stackoverflow.com/questions/32759712/how-to-find-the-closest-word-to-a-vector-using-word2vec

#required python libraries
#pip install gensim
#pip install numpy

import re
import random
import pathlib
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

    def mostSimilarWords(self, word, topN=10):
        return self.word_vecs.most_similar(word, topn=topN)

    def mostSimilarWordsFromVector(self, vector, topN = 10):
        return self.word_vecs.most_similar(positive=[vector], topn=topN)

    def leastSimilarWords(self, word):
        return list(reversed(self.word_vecs.most_similar(word, topn=sys.maxsize)))[:10]
    
    def randomWord(self):
        randomList = self.mostSimilarWordsFromVector(self.word_vecs[random.randint(0,len(self.word_vecs)-1)])
        randomSet = random.choice(randomList)
        return randomSet[0]

global processer

folder = str(pathlib.Path(__file__).parent.resolve()).replace("\\","/")
processer = ProcessWordVectors(f"{folder}/word2vec.model")

#Returns the resulting vector from an equation specified by a string
def returnVectorFromStringEquation(wordsList, equationsList):
    vectorReturn    = processer.getWordVector(wordsList[0])
    if (len(equationsList) > 0):
        for x in range(1, len(wordsList)):
            if (equationsList[x - 1] == "+"):
                vectorReturn    = np.add(vectorReturn, processer.getWordVector(wordsList[x]))
                continue;
            vectorReturn    = np.subtract(vectorReturn, processer.getWordVector(wordsList[x]));
    return vectorReturn

#Turns user input into a word list that can be processed by other functions
def processUserInput(stringEntered: str):
    wordList = re.split(r'[+-]', stringEntered)
    for x in range(len(wordList)):
        wordList[x] = wordList[x].strip()
    return wordList

#Formats the returned data and prints it neatly
def printWordList(wordsList, filterList):
    stringReturn    = ""
    for wordSet in wordsList:
        (wordString, numMatch)  = wordSet
        if (wordString in filterList):
            continue
        numMatch    = np.floor(numMatch*100)
        stringReturn += f'[ {wordString} : {numMatch}% ], '
    return stringReturn

#Handles user inputs and user prompts
def startProcesses(stringEntered):
        if (stringEntered):
            wordList    = processUserInput(stringEntered)
            return printWordList(processer.mostSimilarWordsFromVector(returnVectorFromStringEquation(wordList, re.findall(r'[+-]', stringEntered))), wordList)

#Takes in two words and returns a percentage on how similar they are
def compareWords(word1, word2):
    if (not word1 or not word2):
        return "None"
    return f'{word1} and {word2} are {np.floor(processer.getSimilarity(word1, word2)*100)}% similar'

def listWordSimilarity(word):
    if (word):
        wordList = processUserInput(word)
        return printWordList(processer.mostSimilarWords(word), wordList)

def listWordDisimilarity(word):
    if (word):
        wordList = processUserInput(word)
        return printWordList(processer.leastSimilarWords(word), wordList)
def getRandomWord():
    word = processer.randomWord()
    return word


#WORKSPACE
if __name__ == "__main__":
    stringEntered = None
    startProcesses(stringEntered);
