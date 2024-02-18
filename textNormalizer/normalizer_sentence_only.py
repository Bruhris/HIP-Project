from genericpath import exists, isfile
import io
from msilib.schema import Directory
import os
from os import listdir, mkdir, rmdir
import shutil
from typing import final
import spacy
import string
import time

#This version of normalier tries to include propper sentences only.
#currently not 100% accurate. May cause possible issues.

# https://spacy.io/usage/linguistic-features#lemmatization
# https://www.projectpro.io/recipes/use-spacy-lemmatizer
# list of stop words: https://github.com/igorbrigadir/stopwords/blob/master/en/terrier.txt


global stop_words, word_of_interest, phrases_words, phrases_replacement

#                                   Feel free to tweak around those setting variables
#                 CHARACTER REPLACEMENT LOGICS
global DOT_REPLACEMENT_STRING, CHAPTER_REPLACEMENT_STRING 
DOT_REPLACEMENT_STRING = '_0_' #  _DOT_                   what is used to replace xxx.xxx etc.?
PUNCTUATION_IN_BRACKETS_REPLACEMENT_STRING = ';' #  ;       what is used to replace period marks in brackets/quotes?
CHAPTER_REPLACEMENT_STRING = '' #  _CHAPTER_                what is used to replace the chapter symbols?
#                 LINE SPLITTING AND PROCESSING LOGICS
global IDENTIFICATION_WINDOW, IDENTIFICATION_THRESHOLD, RULE_OUT_CODELIKE_SENTENCES, CONSECUTIVE_WORDS_CLASSIFIED_AS_TEXT, VARIABLE_REMOVAL_RANGE
global END_SENTENCE_CAPITALIZED_FIRST_WORD, REMOVE_QUOTES, REMOVE_BRACKETS
# when  window = 2 , the section of lines considered looks like this:
# line
# line
# CURRENT_LINE
# line
# line
# if  >= identificationThreshold lines of texts in the window has been identified as code, the current line is ommitted.
IDENTIFICATION_WINDOW = 3
IDENTIFICATION_THRESHOLD = 4 # it is really recommended that threshold <= window + 1
RULE_OUT_CODELIKE_SENTENCES = False # if a sentence is considered code, should it be excluded even if the surrounding lines of code does not reach threshold?
CONSECUTIVE_WORDS_CLASSIFIED_AS_TEXT = 5 # a line should be considered as text if max consecutive amount of words in the line >= this number 
VARIABLE_REMOVAL_RANGE = [10, 100] # record variable declaration [0] lines ahead, and variable memorized would be forgotten after [1] lines.
END_SENTENCE_CAPITALIZED_FIRST_WORD = False # if a line starts with a caplitalized character, shall we identify it as the start of a new sentence?
REMOVE_QUOTES = True # shall we exclude whatever is in quotes? (as well as the double quote itself)
REMOVE_BRACKETS = True # shall we remove everything in brackets? (as well as the brackets itself)
#                 SAVING LOGICS
global REPLACE_PHRASES_AFTER_LEMMA, THRESHOLD_WORD_AMOUNT
# should we replace phrases again just before saving?
REPLACE_PHRASES_AFTER_LEMMA = False
# how many words/phrases in words_of_interest.txt/phrases.txt must be a sentence in order for it to be saved?
THRESHOLD_WORD_AMOUNT = 0
#                 DEBUGGING
global PRINT_DEBUG_MESSAGE_VARIABLE_DELETION
PRINT_DEBUG_MESSAGE_VARIABLE_DELETION = False






nlp = spacy.load("en_core_web_sm")
load_model = spacy.load('en_core_web_sm', disable = ['parser','ner'])

def validateTextOrArgument(text, funcType):
      #this checks if a text looks like an argument for function call, for loop / if statement etc.
      text = text.strip()
      if funcType in "elif while for switch": #(else) if or elif, just in case
            return False
      else:
            if text.count(",") == 0:
                  if text.count("(") > 0:
                        return False # we do not see bracket embedded in other brackets in a normal text!
                  elif text.count(" ") <= 2:
                        #String blah_blah    const string &str
                        return False
            else:
                  # more than 1 argument: recurssive call to this function to check each argument
                  for arg in text.split(","):
                        if validateTextOrArgument(arg, funcType) == True:
                              return True
                  return False
      return True
def validateSentenceOrCode(text):
      if len(text) == 0:
            # empty lines are treated as code, as lines with too many empty lines around usually isn't helpful.
            return False
      if text.startswith("#include"):
            return False
      if text.startswith("using namespace"):
            return False
      if text[-1] == ";":
            return False
      # test for consecutive words
      max_consecutive_words = 0
      curr_consecutive_words = 0
      for word in text.split():
            if word.isalpha():
                  curr_consecutive_words += 1
                  max_consecutive_words = max(max_consecutive_words, curr_consecutive_words)
            else:
                  curr_consecutive_words = 0
      if max_consecutive_words >= CONSECUTIVE_WORDS_CLASSIFIED_AS_TEXT:
            return True
      # see if the text contains significant code notations
      identifiers = ["//", "()", "{", "}"]
      for identifier in identifiers:
            if identifier in text:
                  return False
      # loop through the line and determine if a bracket is a part of function call or a bracket in text
      param = ""
      funcType = ""
      lastCharacter = ' '
      lastCharBeforeBracket = ' '
      layerBrackets = 0
      for charact in text:
            if charact == "(":
                  if layerBrackets == 0:
                        lastCharBeforeBracket = lastCharacter
                  layerBrackets += 1
                  param = param.strip().split()
                  if len(param) > 0:
                        funcType = param[-1].lower()
                  param = ""
            elif charact == ")":
                  layerBrackets -= 1
                  if layerBrackets == 0 and lastCharBeforeBracket != " " and (validateTextOrArgument(param, funcType) is False):
                        # the outermost bracket does not follow a space, as usually seen in text; and what's inside the bracket seems to be valid parameters/arguments.
                        return False
            else:
                  param += charact
            lastCharacter = charact
      return True
def variable_char(character):
      return (character.isalpha()) or (character == "_")
def remove_code(para):
      # input: original corpus
      # output: text with all codes removed
      results = []
      
      para_split = para.split("\n")
      para_split.append("END PARAGRAPH") # this would NEVER appear in result, but as a fix that guarantees the very last sentence is fully processed.

      # generate the list that stores information about original sentence (text or code)
      sentenceLines = []
      for i in range(len(para_split)):
            sentenceLines.append(validateSentenceOrCode(para_split[i]))
      
      variableDeclarations = {}
      # the word immediately after a key word is also considered variable
      keyWords = ["new", "Class", "Struct"]
      wrapped_brackets = [0, -1] # bracket, double quote
      for i in range(len(para_split)):
            if len(para_split[i]) == 0:
                  # reset bracket/quote amounts for new paragraph, just in case
                  wrapped_brackets = [0, -1]
            wordCache = ""
            wordCacheLast = ""
            varDeclaredInCurrLine = []
            shouldStartNewWord = False
            keyWordCaptured = False
            # this loop is used to get variable declared in this line, if any
            j = 0
            while j < len(para_split[i]):
                  currChar = para_split[i][j]
                  if variable_char(currChar):
                        if shouldStartNewWord:
                              shouldStartNewWord = False
                              wordCacheLast = wordCache
                              wordCache = ""
                        wordCache += currChar
                  else:
                        if keyWordCaptured:
                              keyWordCaptured = False
                              if (len(wordCache) > 0):
                                    varDeclaredInCurrLine.append(wordCache)
                                    if PRINT_DEBUG_MESSAGE_VARIABLE_DELETION:
                                          print("Line " + str(i + 1) + ", variable (class) declaration: " + wordCache)
                        shouldStartNewWord = True
                        if wordCache in keyWords:
                              keyWordCaptured = True
                        if (currChar == "="):
                              # record the variable name declared. Also accounts for += *= etc
                              if (len(wordCache) > 0):
                                    varDeclaredInCurrLine.append(wordCache)
                                    if PRINT_DEBUG_MESSAGE_VARIABLE_DELETION:
                                          print("Line " + str(i + 1) + ", variable declaration: " + wordCache)
                              # record the type name of the variable. Only capitalized custom type (no int, char etc)
                              if (len(wordCacheLast) > 0) and wordCacheLast[0].isupper():
                                    varDeclaredInCurrLine.append(wordCacheLast)
                                    if PRINT_DEBUG_MESSAGE_VARIABLE_DELETION:
                                          print("Line " + str(i + 1) + ", variable declaration: " + wordCacheLast)
                        elif (currChar == "<"):
                              if (len(wordCache) > 0) and (sentenceLines[i] is False):
                                    # pd = dynamic_cast<CDerived*>(pba);
                                    # dynamic_cast is recorded
                                    varDeclaredInCurrLine.append(wordCache)
                                    if PRINT_DEBUG_MESSAGE_VARIABLE_DELETION:
                                          print("Line " + str(i + 1) + ", variable (class) declaration: " + wordCache)
                  j += 1
            if len(varDeclaredInCurrLine) > 0:
                  variableDeclarations[i] = varDeclaredInCurrLine
            # this loop is used to regulate bracket/quotes
            j = 0
            while j < len(para_split[i]):
                  # count the number of quotes/brackets, remove it according to need
                  if currChar == '(':
                        wrapped_brackets[0] += 1
                        if REMOVE_BRACKETS:
                              para_split[i] = para_split[i][:j] + para_split[i][j + 1:]
                              j -= 1
                  elif currChar == ')':
                        wrapped_brackets[0] -= 1
                        if REMOVE_BRACKETS:
                              para_split[i] = para_split[i][:j] + para_split[i][j + 1:]
                              j -= 1
                  elif currChar == '\"':
                        wrapped_brackets[1] = wrapped_brackets[1] * -1
                        if REMOVE_QUOTES:
                              para_split[i] = para_split[i][:j] + para_split[i][j + 1:]
                              j -= 1
                  # if the character is in a bracket/quote and should be removed 
                  elif (wrapped_brackets[1] > 0) and REMOVE_QUOTES:
                        para_split[i] = para_split[i][:j] + para_split[i][j + 1:]
                        j -= 1
                  elif (wrapped_brackets[0] > 0) and REMOVE_BRACKETS:
                        para_split[i] = para_split[i][:j] + para_split[i][j + 1:]
                        j -= 1
                  # if the dot is embedded in brackets/quotes and not removed, change it so that it does not mess up with sentence identification
                  elif currChar == '.' and max(wrapped_brackets) > 0:
                        # replace .'s in quotes/brackets with replacement string
                        if (j + 1 < len(para_split[i])) and ((para_split[i][j + 1].isalnum()) or (para_split[i][j + 1] in ",")):
                              # punctuation IS NOT the last character in the line; next character is alnum
                              # notations such as e.g., are also considered
                              para_split[i] = para_split[i][:j] + DOT_REPLACEMENT_STRING + para_split[i][j + 1:]
                              j += len(DOT_REPLACEMENT_STRING) - 1
                        else:
                              # next character is alnum OR punctuation IS the last character in the line
                              para_split[i] = para_split[i][:j] + PUNCTUATION_IN_BRACKETS_REPLACEMENT_STRING + para_split[i][j + 1:]
                              j += len(PUNCTUATION_IN_BRACKETS_REPLACEMENT_STRING) - 1
                  j += 1
      
      identified = 0
      wrapped_braces = 0
      # initialize how many of the first few lines are identified as code.
      # Not that important as not many corpus start with code, but good to cover it up just in case.
      for i in range(min(IDENTIFICATION_WINDOW, len(para_split))):
            if sentenceLines[i] is False:
                  identified += 1
      varNames = {}
      # initialize the variables declared in the first few lines.
      # Not that important as not many corpus start with code, but good to cover it up just in case.
      for i in range(min(VARIABLE_REMOVAL_RANGE[0], len(para_split))):
            if i in variableDeclarations:
                  for wd in variableDeclarations[i]:
                        varNames[wd] = VARIABLE_REMOVAL_RANGE[1] - (i + 1 - VARIABLE_REMOVAL_RANGE[0])
      for i in range(len(para_split)):
            currLine = para_split[i].strip()
            currLineIsCode = (sentenceLines[i] is False) or (wrapped_braces > 0) # if this is wrapped in a braces, then this is a part of code for sure
            # connect two lines with a dash in between, as it indicates a word being split up into two lines
            if len(currLine) >= 1:
                  if currLine[-1] == '-':
                        # programm-
                        # ing
                        if len(para_split) <= i + 1:
                              currLine = currLine[:-1] # just in case the last line ends with a "-", this removes the "-"
                        else:
                              para_split[i + 1] = currLine[:-1] + para_split[i + 1]
                              para_split[i] = ""
                              currLine = ""
            # load variable names that is VARIABLE_REMOVAL_RANGE[0] lines ahead of current line
            addIndex = i + VARIABLE_REMOVAL_RANGE[0]
            if addIndex in variableDeclarations:
                  for wd in variableDeclarations[addIndex]:
                        varNames[wd] = VARIABLE_REMOVAL_RANGE[1]
                        if PRINT_DEBUG_MESSAGE_VARIABLE_DELETION:
                              print("Line " + str(i + 1) + ", added variable: " + wd)
            # remove variables that has been declared too far ahead and should be forgotten. APPLIES NOT TO CODE LINES!
            if sentenceLines[i]:
                  varNameToRemove = []
                  for varName in varNames:
                        varNames[varName] -= 1
                        if varNames[varName] <= 0:
                              varNameToRemove.append(varName)
                  for varName in varNameToRemove:
                        varNames.pop(varName)
                        if PRINT_DEBUG_MESSAGE_VARIABLE_DELETION:
                              print("Line " + str(i + 1) + ", removed variable: " + varName)
            # remove all variable names in the sentence
            j = len(currLine)
            textCache = ""
            while j > 0:
                  j -= 1
                  if variable_char(currLine[j]):
                        textCache = currLine[j] + textCache
                        if (textCache in varNames) and ((j - 1 < 0) or (variable_char(currLine[j - 1]) is False)):
                              if PRINT_DEBUG_MESSAGE_VARIABLE_DELETION:
                                    print("Removed word: " + textCache + " in sentence:||| " + currLine)
                              # remove the variable name from the line
                              currLine = currLine[:j] + currLine[j + len(textCache):]
                              if PRINT_DEBUG_MESSAGE_VARIABLE_DELETION:
                                    print("Removed word: " + textCache + " in sentence:||| " + currLine)
                  else:
                        textCache = ""
            # get the amount of code lines in the window; sliding window technique to reduce lagg
            idxOutOfWindow = i - IDENTIFICATION_WINDOW - 1
            if (idxOutOfWindow >= 0) and (sentenceLines[idxOutOfWindow] is False):
                  identified -= 1
            idxInWindow = i + IDENTIFICATION_WINDOW
            if (idxInWindow < len(para_split)) and (sentenceLines[idxInWindow] is False):
                  identified += 1
            # check if this line is a part of code
            if currLine.count("{") > 0:
                  wrapped_braces += currLine.count("{")
            if currLine.count("}") > 0:
                  wrapped_braces -= currLine.count("}")
            if identified >= IDENTIFICATION_THRESHOLD:
                  # the surrounding lines are mostly codes. This line is most likely pure code as well.
                  currLineIsCode = True
            else:
                  currLineIsCode = currLineIsCode and RULE_OUT_CODELIKE_SENTENCES
            if currLineIsCode:
                  # code: current text buffer is a finished sentence.
                  currLine = "END PARAGRAPH"
            elif currLine.endswith("."):
                  # regulate sentences
                  currLine += " END PARAGRAPH"
            # replace the dot in xxx.xxx
            j = 0
            while j < len(currLine) - 1:
                  # this is before a '.' in the middle of a line; accounts for function notations such as "aaa.xxx()" or "1.25", but not "blah blah. Blah blah"
                  if (currLine[j] == ".") and (currLine[j + 1] != " "):
                        currLine = currLine[:j] + DOT_REPLACEMENT_STRING + currLine[j + 1:]
                        j += len(DOT_REPLACEMENT_STRING) - 1
                  j += 1
            currLine = currLine.replace("§", CHAPTER_REPLACEMENT_STRING).strip()
            results.append(currLine)
      return '\n'.join(results)
def split_paragraph(para):
      # input: a paragraph
      # output: an array containing sentences extracted

      para_split = para.split("\n")
      text_buffer = ""
      sentences = []
      
      for i in range(len(para_split)):
            currLine = para_split[i].strip()
            splitcurrLine = currLine.split(".")
            # loop through all sentences split at ". " in the current line
            # this is used instead of for j in range... 
            # because we could expect to have ["", "blah _DOT_ blah"] and the first element doesn't count
            currSplitIdx = 0
            for currLine_splt in splitcurrLine:
                  currLine_splt = currLine_splt.strip()
                  if len(currLine_splt) < 1:
                        continue
                  shouldEndSentence = False # should this mark the end of last sentence?
                  shouldIncludeCurrent = True #should 
                  if currLine_splt == "END PARAGRAPH":
                        #seems to be a piece of code or is the dummy line appended
                        shouldEndSentence = True
                        shouldIncludeCurrent = False
                  else:
                        if currSplitIdx > 0: # this part follows a ". "
                              shouldEndSentence = True
                        elif currLine_splt[0].isupper():
                              if ((len(currLine_splt) > 1) and (currLine_splt[1].isalpha()) and # prevents things such as C++ being recognized as the start of a new sentence
                                          (len(text_buffer) > 0) and ((text_buffer[-1] in string.punctuation) is False)): # prevents blah blah: \n Something
                                    shouldEndSentence = END_SENTENCE_CAPITALIZED_FIRST_WORD
                  if shouldEndSentence:
                        if len(text_buffer) > 0 and text_buffer[0].isupper():
                              if text_buffer.count(" ") >= 2:
                                    sentences.append(text_buffer + ".")
                        if currLine_splt == "END PARAGRAPH":
                              sentences.append('')
                        text_buffer = ""
                  if shouldIncludeCurrent:
                        if len(text_buffer) > 0:
                              text_buffer += " "
                        text_buffer += currLine_splt
                  currSplitIdx += 1
      return sentences
def simple_regulateStr(toProcess):
      # input: an entire corpus waiting to be regulated
      # output: a list of lemmatized & regulated strings
      #lowercase, tokenized it, used lemmatization
      lemma = []
      #split by paragraph so that the model does not become too big and too memory expensive
      if "\n" in toProcess:
            sentences = split_paragraph(toProcess)
      else:
            sentences = [toProcess]
      for sentence in sentences:
            sentence = sentence.strip().lower()
            if len(sentence) < 1:
                  continue
            tokens = load_model(sentence)
            for token in tokens:
                  #lemma.append(lemmatizer.lemmatize(token.text))
                  lemma.append(token.lemma_)
            
      #end token&lemma
      return lemma
def replace_phrases(toReplace, phrases_words, phrases_replacement):
      splitted = []
      possible_phrases = []
      for word in toReplace:
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
      return splitted
def regulateStr(toProcess, stop_words, phrases_words, phrases_replacement):
      # input: string, list of stop words(removed from string), phrases_words -> phrases_replacement
      #     phrases_words and phrases_replacement should have the same length
      # output: regulated string  
      # added bigrams and then removed all the stop words
      lemma = simple_regulateStr(toProcess)
      toJoin = []
      splitted = replace_phrases(lemma, phrases_words=phrases_words, phrases_replacement=phrases_replacement)
      isLastWordStopword = False
      for word in splitted:
            if word in stop_words:
                  isLastWordStopword = True
                  continue
            if isLastWordStopword:
                  isLastWordStopword = False
                  if (word in string.punctuation):
                        continue
                        #However, blah blah blah
                        #however got removed by stop word, no reason to keep the punctuation as a first token in a processed sentence
            toJoin.append(word)
      return ' '.join(toJoin)
def ensureFolderExists(dir):
      if exists(dir) is False:
            print(dir + " does not exist. Creating folder.")
            mkdir(dir)
def trimSentence(original, word_of_interest_set, phrases_replacement_set, keepPunctuation):
      shouldAppend = True
      splitted = original.split()
      finalLemma = []
      punctuations = ['\'', '\"', ',', '.', '?', '!', ';', ':']
      if len(original) == 0:
            shouldAppend = False
      else:
            amountWord = 0
            for splitted_frag in splitted:
                  if len(splitted_frag) == 0:
                        continue
                  currPunctuation = None
                  if splitted_frag[-1] in punctuations:
                        currPunctuation = splitted_frag[-1]
                        splitted_frag = splitted_frag[:-1]
                  if (splitted_frag.isalpha()):
                        amountWord += 1
                  shouldKeep = False
                  if (splitted_frag.isalpha()) and (len(splitted_frag) >= 2):
                        shouldKeep = True
                  elif (splitted_frag in ". c++"):
                        # write only completely alphabetic words, c++ and period marks
                        shouldKeep = True
                  elif (splitted_frag in phrases_replacement_set):
                        shouldKeep = True
                  if shouldKeep:
                        finalLemma.append(splitted_frag)
                  if (currPunctuation != None) and (keepPunctuation):
                        if (len(finalLemma) == 0) or (finalLemma[-1].isalpha()):
                              finalLemma.append(currPunctuation)
            if amountWord < 2:
                  # if there's only one word after lemmatization, the sentence is meaningless to keep
                  shouldAppend = False
      if shouldAppend:
            # replace phrases again after removing stop word etc if needed
            if REPLACE_PHRASES_AFTER_LEMMA:
                  finalLemma = replace_phrases(finalLemma, phrases_words, phrases_replacement)
      # decide if the sentence contains enough word/phrases
      wordOccured = set()
      containsEnoughWord = False
      for word in finalLemma:
            if (word in word_of_interest_set) or (word in phrases_replacement_set):
                  wordOccured.add(word)
            if len(wordOccured) >= THRESHOLD_WORD_AMOUNT:
                  containsEnoughWord = True
                  break
      shouldAppend = shouldAppend and containsEnoughWord
      return finalLemma, shouldAppend
def regulate(fileOutAll, dir, dirToSave, dirToSaveSplit, dirIntermediate):
      # input: 3 directions to load/save joined/save split; stop words, raw phrases, phrases_replacement(with "_" instead of " ")
      # ouput: none
      # uses recurssion to loop though all txt files, regulate and save them

      # cache joined phrases as well as interested words into sets
      word_of_interest_set = set()
      for woi in word_of_interest:
            word_of_interest_set.add(woi)
      phrases_replacement_set = set()
      for prp in phrases_replacement:
            phrases_replacement_set.add(prp)
      
      print("Opening directory:", dir + dirIntermediate)
      ensureFolderExists(dirToSave)
      for i in listdir(dir  + dirIntermediate):
            d = dir + dirIntermediate + i
            directoryToSaveSentence = dirToSave + "sentences/" + dirIntermediate
            directoryToSaveSentenceTrimmed = dirToSave + "sentencesTrimmed/" + dirIntermediate
            directoryToSaveLemmaSen = dirToSave + "lemmatized/" + dirIntermediate
            if isfile(d):
                  print("Regulating file:", d)
                  if i.endswith(".txt") is False:
                        continue
                  fileIn = io.open(d, 'r', encoding='utf-8')
                  original = fileIn.read()
                  original_regulated = (original.replace("“", "\"").replace("”", "\"").replace("‘", "\'").replace("’", "\'").replace("\'\'", "\"")  # regulate quotes
                                    .replace("", " ").replace("•", ". END PARAGRAPH. ")                                                            # regulate formatting characters
                                    .replace("++", "plus_plus").replace("--", "minus_minus").replace("->", "arrow_operator")                        # regulate special signs
                                    .replace("?", ".").replace("!", ".")                                                                           # regulate punctuations
                                    .replace("U.S.A.", "The United States of America").replace("U.S.", "The United States"))
                  original_regulated = remove_code(original_regulated)
                  fileIn.close()
                  ensureFolderExists(directoryToSaveSentence)
                  ensureFolderExists(directoryToSaveSentenceTrimmed)
                  ensureFolderExists(directoryToSaveLemmaSen)
                  splitPara = split_paragraph(original_regulated)
                  splitPara_toKeep = [] # which line should be kept?
                  print("  generating lemmatized sentence file...")
                  timeLast = time.time() * 1000
                  lemma_splitPara = []
                  for sentence in splitPara:
                        # regulate the sentence: lowercase, replace .'s and phrases etc
                        toAppend = regulateStr(sentence, stop_words=stop_words, phrases_words=phrases_words, phrases_replacement=phrases_replacement)
                        finalLemma, shouldAppend = trimSentence(toAppend, word_of_interest_set, phrases_replacement_set, False)

                        splitPara_toKeep.append(shouldAppend) # is this sentence good to keep?
                        if shouldAppend:
                              lemma_splitPara.append(' '.join(finalLemma))
                  fileOut = io.open(directoryToSaveLemmaSen + i, 'w', encoding='utf-8')
                  fileOut.write('\n'.join(lemma_splitPara))
                  fileOutAll.write('\n'.join(lemma_splitPara) + '\n')
                  fileOut.close()
                  print("    Time elapsed: " + str(time.time() * 1000 - timeLast) + "ms")
                  
                  print("  generating sentence file...")
                  timeLast = time.time() * 1000
                  splitPara_toPrint = []
                  for j in range(len(splitPara)):
                        if splitPara_toKeep[j]:
                              splitPara_toPrint.append(splitPara[j])
                  fileOut = io.open(directoryToSaveSentence + i, 'w', encoding='utf-8')
                  fileOut.write('\n'.join(splitPara_toPrint))
                  fileOut.close()
                  print("    Time elapsed: " + str(time.time() * 1000 - timeLast) + "ms")

                  print("  generating trimmed sentence file...")
                  timeLast = time.time() * 1000
                  splitPara_trimmed = []
                  lastDiscarded = True
                  for j in range(len(splitPara)):
                        if splitPara_toKeep[j]:
                              trimmed, shouldAppend = trimSentence(splitPara[j], word_of_interest_set, phrases_replacement_set, True)
                              splitPara_trimmed.append(' '.join(trimmed))
                              lastDiscarded = False
                        else:
                              if lastDiscarded == False:
                                    splitPara_trimmed.append('')
                              lastDiscarded = True
                  fileOut = io.open(directoryToSaveSentenceTrimmed + i, 'w', encoding='utf-8')
                  fileOut.write('\n'.join(splitPara_trimmed))
                  fileOut.close()
                  print("    Time elapsed: " + str(time.time() * 1000 - timeLast) + "ms")
                  #end writing raw sentence split
            else:
                  dirinterm = dirIntermediate + i + "/"
                  regulate(fileOutAll, dir, dirToSave, dirToSaveSplit, dirinterm)


#change the directory according to your preference.
#non-existing directories would be automatically created.
#the algorithm uses recurrsion to find all .txt files in the directory provided and outputs processed files in dir_output, in the same name and intermediate folders as original


def read_info_file(dir):
      # input: a directory
      # output: a list of strings
      # used to read stop words and phrases
      fileIn = io.open(dir, 'r', encoding='utf-8')
      return fileIn.read().splitlines()
stop_words_raw = read_info_file("stop_words.txt")
phrases = read_info_file("phrases.txt")
word_of_interest_raw = read_info_file("words_of_interest.txt")

def simple_phrase_regulator(phrase):
      # input: a phrase (or a word)
      # output: lemmatized and regulated input
      # lowercase, tokenized it, used lemmatization
      lower = phrase.lower()
      # end lowercase
      lemma = []
      toLemma = lower.strip()
      if len(toLemma) >= 1:
            tokens = load_model(toLemma)
            for token in tokens:
                  #lemma.append(lemmatizer.lemmatize(token.text))
                  lemma.append(token.lemma_)
      # end token&lemma
      return lemma
# process stop words and interested words so that they match up with regulated version
# just in case, both lemmatized and original forms are kept
stop_words = []
for res in stop_words_raw:
      stop_words.append(res)
      stop_words.append(' '.join(simple_phrase_regulator(res)))
word_of_interest = []
for res in word_of_interest_raw:
      word_of_interest.append(res)
      word_of_interest.append(' '.join(simple_phrase_regulator(res)))
phrases_words = []
phrases_replacement = []
for phrase in phrases:
      phrases_words.append(phrase.replace('_', ' ').split())
      phrases_words.append(simple_phrase_regulator(phrase.replace('_', ' ')))
      phrases_replacement.append(phrase.replace(' ', '_'))
      phrases_replacement.append(phrase.replace(' ', '_'))
#this converts "_ dot _" back into "_DOT_"
phrases_words.append(["_", "dot", "_"])
phrases_replacement.append("_DOT_")
phrases_words.append(["_", "section", "_"])
phrases_replacement.append("_SECTION_")

print("list of stop words: ")
print(stop_words)
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
dir_output = 'processed/sentence_only/'
dir_output_split = 'split/sentence_only/'
dirToSaveAll = 'processed/sentence_only/allLemmatized.txt'
# # do not replace phrases. only replace _ dot _  and  _ section _
# phrases_words =       [["_", "dot", "_"],      ["_", "section", "_"]]
# phrases_replacement = [DOT_REPLACEMENT_STRING, CHAPTER_REPLACEMENT_STRING]
fileOutAll = io.open(dirToSaveAll, 'w', encoding='utf-8')
regulate(fileOutAll, dir_original, dir_output, dir_output_split, "")
fileOutAll.close()