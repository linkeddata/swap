"""dekeywordizer

    I need to make this operate on streams of tokens
"""

import re

def dekeywordize(inTokens, bareName):
    """remove @keywords designations


    """
    keywordMode = False
    newKeywordMode = False
    keywords = {"a": 1, "is" : 1, "of" : 1, "this" : 1}
    
    for token in inTokens:
        if token[0:1] == '#':
            continue
        if newKeywordMode:
            if token == '.':
                newKeywordMode = False
            elif newKeywordMode == 1:
                keywords[token] = True
                newKeywordMode = 2
            elif newKeywordMode == 2 and token == ',':
                newKeywordMode = 1
            else:
                raise ValueError('I can\'t parse something with regard to keywords')
        else:
            if (token == '@keywords') or \
               (token == 'keywords' and keywordMode and 'keywords' in keywords):
                keywordMode = True
                newKeywordMode = 1
                keywords = {}
            else:
                if keywordMode:
                    if token in keywords:
                        yield '@' + token
                    elif bareName.match(token):
                        yield ':' + token
                    else:
                        yield token
                else:
                    if token in keywords:
                        yield '@' + token
                    else:
                        yield token

#if __name__ == '__main__':
#    import sys
#    dekeywordize(sys.stdin, sys.stdout)
