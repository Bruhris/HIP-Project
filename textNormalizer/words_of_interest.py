from genericpath import exists, isfile
import io
import os
from os import listdir, mkdir, rmdir
from posixpath import split
import time
from numpy import vectorize

import spacy
from wordfreq import word_frequency

global totalAmount, wordsAndFreq;
totalAmount = 0;
wordsAndFreq = {};


nlp = spacy.load("en_core_web_sm")
load_model = spacy.load('en_core_web_sm', disable = ['parser','ner'])


def getWords(text):
      global totalAmount, wordsAndFreq
      text = " " + text + " "
      word = ""
      for i in range(1, len(text) - 1):
            if (text[i] == "-") and (text[i + 1] == "\n"):
                  i += 1
                  continue
            elif text[i].isalpha():
                  word += text[i].lower()
            else:
                  totalAmount += 1
                  if len(word) >= 2:
                        if word not in wordsAndFreq:
                              wordsAndFreq[word] = 1
                        else:
                              wordsAndFreq[word] += 1
                  word = ""

def regulate(dir):
      print("Opening directory:", dir)
      for i in listdir(dir):
            d = dir + i
            if isfile(d):
                print("reading into file:", d)
                if i.endswith(".txt") is True:
                    fileIn = io.open(d, 'r', encoding='utf-8')
                    original = fileIn.read()
                    fileIn.close()
                    print("  reading words in file...")
                    timeLast = time.time() * 1000
                    getWords(original)
                    print("    Time elapsed: " + str(time.time() * 1000 - timeLast) + "ms")
                    #end writing in tosave
            else:
                d += "/"
                regulate(d)



#process phrases so that they match up with regulated version
dir_original = 'WOI_src/'
dir_save = 'words_of_interest.txt'
regulate(dir_original)

print("-> generating candidate word list...")
timeLast = time.time() * 1000
topCandidates = []

for word in wordsAndFreq:
      occurance = wordsAndFreq[word]
      curr_freq = occurance / totalAmount
      global_freq = word_frequency(word, 'en')
      if (curr_freq > global_freq) and (global_freq > 1e-12):
            topCandidates.append((1 / (curr_freq - global_freq), word))
topCandidates = sorted(topCandidates)
print("    Time elapsed: " + str(time.time() * 1000 - timeLast) + "ms")



print("-> lemmatizing and saving candidate word list...")
timeLast = time.time() * 1000
# lemmatize
printed_words = set()
fileOut = io.open(dir_save, 'w', encoding='utf-8')
for i in range(len(topCandidates)):
      tokens = load_model(topCandidates[i][1])
      wd = tokens[0].lemma_
      if wd not in printed_words:
            printed_words.add(wd)
            fileOut.write(wd + "\n")
fileOut.close()
print("    Time elapsed: " + str(time.time() * 1000 - timeLast) + "ms")




while True:
      word = input()
      if word == "exit_":
            break
      occurance = 0
      if word in wordsAndFreq:
            occurance = wordsAndFreq[word]
      curr_freq = occurance / totalAmount
      global_freq = word_frequency(word, 'en')
      print(str(curr_freq) + "//" + str(global_freq))
      print(word + ": " + str(curr_freq - global_freq))