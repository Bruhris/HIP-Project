Throw all txt files to preprocess in the original, the program can also search into subdirectories.

The processed folder should contain all outputs from normalizer.py and normalizer_sentence_only.py

normalizer.py: only lemmatize etc. do not consider code/sentence. saved directly in processed/
normalizer_sentence_only.py: considers sentences. Saves non-code sentences that contains phrases and words of interest in processed/sentence_only/sentence.
                             it then lemmatize the sentences and saves such sentences which are long enough into processed/sentence_only/sentence/lemmatized, with short words/words that are not purely alphabetic removed.

A file original/test/test1.txt would be saved in directories below:
normalizer.py:  		processed/test/test1.txt
normalizer_sentence_only.py:  	processed/sentence_only/sentence/test/test1.txt  and  processed/sentence_only/lemmatized/test/test1.txt


words_of_interest.py: compares the occurence frequency of each word in woi/ folder with overall frequency in english language.
Then it saves all words with frequency difference > 0 into the file, with descending order of difference