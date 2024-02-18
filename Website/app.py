from mimetypes import guess_all_extensions
from pyexpat import model
from flask import Flask, render_template, request
from src import processWordVectors, guessingGame

app = Flask(__name__)

#<<GUESSING GAME>>

guessingGame.getRandomWord();
guessingGame.getRandomWord()

@app.route("/", methods=["GET",'POST'])
def load():
    dict_guesses = {}
    msgtext = ""
    reg     = False
    hint_text_temp = ""
    guess = request.form.get('guess')
    if (request.form.get('restart-btn')):
        return render_template("index.html", result=f'Unfortunate! The word you failed to guess was: "{guessingGame.resetGuessingGame()}"')

    if not reg:
        msgtext = "That word is not registered"
    if guess == '':
        msgtext = "You did not type a word."

    if (request.form.get("hint")):
        hint = guessingGame.provideHint()
        if hint == '1':
            msgtext = f'No sentence contains both words in the corpus'
            dict_guesses, reg = guessingGame.cacheUserGuess("asadasdsa")
        elif hint == None:
            msgtext = "Hint requires a recent guess"
        else:
            dict_guesses, reg = guessingGame.cacheUserGuess("asadasdsa")
            hint_text_temp = hint



    if guessingGame.checkUserGuess(guess):
        return render_template('index.html', result=f'You guessed correct! The word was: "{guessingGame.resetGuessingGame()}"')
    else:
        if guess != None:
            dict_guesses, reg   = guessingGame.cacheUserGuess(guess)

    if not reg:
        msgtext = "That word is not registered"
    if guess == '':
        msgtext = "You did not type a word."
        dict_guesses, reg = guessingGame.cacheUserGuess(guess)

    return render_template(
        'index.html',
        message=msgtext,
        hint_text=hint_text_temp,
        data=list(dict_guesses.keys()),
        similarities=list(dict_guesses.values()),
        closestguess=guessingGame.getClosestGuess()
    )

#<<GUESSING_GAME_END>>

@app.route("/VectorMath", methods=["GET","POST"])
def getInput():
    text = request.form.get('equation')
    try:
        outputText = processWordVectors.startProcesses(text)
    except KeyError:
        outputText = "That word is not recognized. Please try again."
    return render_template('VectorMath.html', data=outputText)

@app.route("/WordSim", methods=["GET","POST"])
def wordsimilarity():
    word1 = request.form.get('word1')
    word2 = request.form.get('word2')
    try:
        outputText = processWordVectors.compareWords(word1, word2)
    except KeyError:
        outputText = "That word is not recognized. Please try again."
    return render_template('similarity.html', data=outputText)

@app.route("/SimilarWords", methods=["GET","POST"])
def similarWords():
    word = request.form.get('word')
    option = request.form.get('optionselect')
    if option == "MostSimilar":
        try:
            outputText = processWordVectors.listWordSimilarity(word)
        except KeyError:
            outputText = "That word is not recognized. Please try again."
        return render_template('SimilarWords.html', data=outputText)
    elif option == "LeastSimilar":
        try:
            outputText = processWordVectors.listWordDisimilarity(word)
        except KeyError:
            outputText = "That word is not recognized. Please try again."
        return render_template('SimilarWords.html', data=outputText)
    return render_template('SimilarWords.html')

if __name__ == "__main__":
    app.run(debug=True)
