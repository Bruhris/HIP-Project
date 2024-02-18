import sys
import pathlib
import src.processWordVectors as processWordVectors
import random
import operator

#SHARED_VALUES
global wordToGuess

#MODULAR_FUNCTIONS
wordProcesser   = processWordVectors.processer
closesetGuess   = ['', 0]
guesses = {}

wordsOfInterest = []
filtered_sentences = []


with open("textNormalizer/processed/sentence_only/all_sentences.txt", encoding="utf8") as file:
    data = file.read()
    sentences = data.split('.')
    for i in range(len(sentences)):
        if len(sentences[i].replace(' ', '')) < 500:
            filtered_sentences.append(sentences[i].replace('\n', ''))




#[Initializes values]
def __init__():
    folder = str(pathlib.Path(__file__).parent.resolve()).replace("\\","/")
    with open(f"{folder}/words_of_interest.txt") as textFile:
        for line in textFile:
            try:
                line = line.lower().strip().replace('\n','')
                wordProcesser.getWordVector(line)
            except:
                pass
            else:
                wordsOfInterest.append(line)
    return

#[This function returns a random word that the player will need to guess]
def getRandomWord():
    global wordToGuess
    wordToGuess = random.choice(wordsOfInterest)
    print(wordToGuess)
    return wordToGuess



#[Compares user guess to the answer]
def checkUserGuess(userGuess: str):
    return (userGuess == wordToGuess)

#[Caches user guess so that it can calculate the similarity, returns all guesses string]
def cacheUserGuess(userGuess: str) -> str:
    global guesses
    reg = True
    userGuess = userGuess.lower().strip()
    if (userGuess):
        similarityPercent = 0;
        try:
            similarityPercent = round(wordProcesser.getSimilarity(wordToGuess, userGuess)*100, 2)
        except:
            reg = False
        else:
            if (similarityPercent > closesetGuess[1]):
                closesetGuess[0], closesetGuess[1] = userGuess, similarityPercent
            guesses[userGuess] = similarityPercent
            guesses = dict(sorted(guesses.items(), key=operator.itemgetter(1), reverse=True))
    return guesses, reg

#Provides a sentence with chosen word and recent guess
def provideHint():
    similar_sentences = []
    if len(closesetGuess[0]) > 0:
        for sentence in filtered_sentences:
            if wordToGuess in sentence and closesetGuess[0] in sentence:
                similar_sentences.append(sentence)
        if len(similar_sentences) == 0:
            return '1'
        elif len(similar_sentences) == 1:
            return similar_sentences[0].replace(wordToGuess, "_"*len(wordToGuess))
        elif len(similar_sentences) > 1:
            return similar_sentences[random.randint(0, len(similar_sentences)-1)].replace(wordToGuess, "_"*len(wordToGuess))
    else:
        pass








#Resets the game
def resetGuessingGame():
    global closesetGuess
    global guesses
    guesses = {}
    closesetGuess   = ['', 0]
    oldWord = wordToGuess
    getRandomWord()
    return oldWord

#[[Returns player's closest guess]]
def getClosestGuess():
    if (not closesetGuess[0]):
        return ''
    return f'Closest guess: "{closesetGuess[0]}" with a similarity of {closesetGuess[1]}%'

#[Returns amount guesses]
def getAmountGuesses():
    return len(guesses)

#WORKSPACE
__init__();
