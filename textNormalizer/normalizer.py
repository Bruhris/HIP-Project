from genericpath import exists, isfile
import io
import os
from os import listdir, mkdir, rmdir
from posixpath import split
import spacy
import shutil
import time
#import nltk
#from nltk.stem import WordNetLemmatizer

#This version of normalier tries to normalize EVERYTHING in the source file.
#The sentence only version tries to only include sentences.

# https://spacy.io/usage/linguistic-features#lemmatization
# https://www.projectpro.io/recipes/use-spacy-lemmatizer
# list of stop words: https://github.com/igorbrigadir/stopwords/blob/master/en/terrier.txt
# list of programming-related phrases: https://github.com/igorbrigadir/stopwords/blob/master/en/terrier.txt

#regulate source txt files
nlp = spacy.load("en_core_web_sm")
load_model = spacy.load('en_core_web_sm', disable = ['parser','ner'])
#lemmatizer = WordNetLemmatizer()
def simple_regulateStr(toProcess):
      #lowercase, tokenized it, used lemmatization
      lowercased = toProcess.lower().replace("“", "\"").replace("”", "\"").replace("‘", "\'").replace("’", "\'")
      #end lowercase
      lemma = []
      for para in lowercased.split("\n\n"):
            tokens = load_model(para.replace("-\n", "").replace("\n", " "))
            for token in tokens:
                  #lemma.append(lemmatizer.lemmatize(token.text))
                  lemma.append(token.lemma_)
      #end token&lemma
      return lemma
def regulateStr(toProcess, stop_words, phrases_words, phrases_replacement):
      #added bigrams and then removed all the stop words
      lemma = simple_regulateStr(toProcess)
      splitted = []
      possible_phrases = []
      for word in lemma:
            next_possible_phrases = []
            splitted.append(word)
            for i in range(len(phrases_words)):
                  next_possible_phrases.append([i, 0])
            for p_p in possible_phrases:
                  #loop through all validating phrases
                  phraseMapItem = phrases_words[p_p[0]]
                  idxCheckWord = p_p[1]
                  if word == phraseMapItem[idxCheckWord]:
                        #if the word of the phrase is validated, but the phrase is not completely validated
                        p_p[1] = idxCheckWord + 1
                        if len(phraseMapItem) <= p_p[1]:
                              #if all words in the phrase has been validated
                              next_possible_phrases = []
                              for i in range(len(phraseMapItem)):
                                    splitted.pop()
                              splitted.append(phrases_replacement[p_p[0]])
                              break
                        else:
                              next_possible_phrases.append(p_p)
            possible_phrases = next_possible_phrases
      #end bigram/phrase
      toJoin = []
      for word in splitted:
            if word in stop_words:
                  continue
            toJoin.append(word)
      return ' '.join(toJoin)
def regulate(dir, dirToSave, dirToSaveSplit, stop_words, phrases_words, phrases_replacement):
      print("Opening directory:", dir)
      if exists(dirToSave) is False:
            mkdir(dirToSave)
      if exists(dirToSaveSplit) is False:
            mkdir(dirToSaveSplit)
      for i in listdir(dir):
            d = dir + i
            dts = dirToSave + i
            dtsspl = dirToSaveSplit + i
            if isfile(d):
                  print("Regulating file:", d)
                  i.endswith(".txt")
                  fileIn = io.open(d, 'r', encoding='utf-8')
                  original = fileIn.read()
                  fileIn.close()
                  index = 1
                  dtsspl = dtsspl[:-4] + "/"
                  if exists(dtsspl) is False:
                        mkdir(dtsspl)
                  allLines = original.split("\n\n")
                  print("  Generating and saving file split by line: " + d + "(" + str(len(allLines)) + "lines/files.)")
                  timeLast = time.time() * 1000
                  paras = []
                  for currLine in allLines:
                        if len(currLine) < 1:
                              continue
                        fileOutSplit = io.open(dtsspl + str(index) + ".txt", 'w', encoding='utf-8')
                        resultStr = regulateStr(currLine, stop_words, phrases_words, phrases_replacement)
                        if len(resultStr) <= 1:
                              continue
                        fileOutSplit.write(resultStr)
                        paras.append(resultStr)
                        fileOutSplit.close()
                        index += 1
                  #end writing in split
                  shutil.make_archive(dirToSaveSplit + i[:-4], format='zip', root_dir=dtsspl)
                  for i in range(1, index):
                      os.remove(dtsspl + str(i) + ".txt")
                  rmdir(dtsspl)
                  print("    Time elapsed: " + str(time.time() * 1000 - timeLast) + "ms")
                  #zip the file so we don't have a headache uploading to github
                  print("  generating processed file...")
                  timeLast = time.time() * 1000
                  fileOut = io.open(dts, 'w', encoding='utf-8')
                  resultStr = ' '.join(paras)
                  fileOut.write(resultStr)
                  fileOut.close()
                  print("    Time elapsed: " + str(time.time() * 1000 - timeLast) + "ms")
                  #end writing in tosave
            else:
                  d += "/"
                  dts += "/"
                  dtsspl += "/"
                  regulate(d, dts, dtsspl, stop_words, phrases_words, phrases_replacement)
      pass

#change the directory according to your preference.
#non-existing directories would be automatically created.
#the algorithm uses recurrsion to find all .txt files in the directory provided and outputs processed files in dir_output, in the same name and intermediate folders as original

def read_info_file(dir):
      fileIn = io.open(dir, 'r', encoding='utf-8')
      return fileIn.read().splitlines()
stop_words = read_info_file("stop_words.txt")
phrases = read_info_file("phrases.txt")


stop_words_regul = []
for res in stop_words:
      stop_words_regul.append(' '.join(simple_regulateStr(res)))
#process stop words so that they match up with regulated version
phrases_words = []
phrases_replacement = []
for phrase in phrases:
      phrases_words.append(simple_regulateStr(phrase))
      phrases_replacement.append(phrase.replace(' ', '_'))
print("list of stop words: ")
print(stop_words_regul)
print("\n")
print("list of phrases: ")
outputStr = ''
for i in range(len(phrases_words)):
      outputStr += str(phrases_words[i])
      outputStr += "->"
      outputStr += str(phrases_replacement[i])
      outputStr += "; "
print(outputStr)
print("\n")
print("\n")
#process phrases so that they match up with regulated version
dir_original = 'original/'
dir_output = 'processed/'
dir_output_split = 'split/'
regulate(dir_original, dir_output, dir_output_split, stop_words_regul, phrases_words=phrases_words, phrases_replacement=phrases_replacement)