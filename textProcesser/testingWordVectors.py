from processWordVectors import processer

testCases   = [
    "function",
    "variable",
    "int",
    "string",
    "boolean",
    "true",
    "false"
]


def startTest():
    for testCase in testCases:
        print(f'{testCase}:')
        for wordSet in processer.mostSimilarWords(testCase):
            wordStr, wordPercent    = wordSet
            print(f'\t{wordStr} : {round(wordPercent*100, 2)}%')
        # print("\nleast Similar:")
        # for wordSet in processer.leastSimilarWords(testCase):
        #     wordStr, wordPercent    = wordSet
        #     print(f'\t{wordStr} : {round(wordPercent*100, 2)}%')

startTest();