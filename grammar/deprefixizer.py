"""deprefixizer

   When we are done with this, it will not have any prefixes
"""

import re
import uripath

def absolutize(uri, baseURI):
    return uripath.join(baseURI, uri)

def deprefixize(inTokens, baseURI, prefixMap, qName, uri, fn=None):
    """remove @keywords designations


    """
    
    prefixMode = 0
    for token in inTokens:
        if token[0:1] == '#':
            continue
        if prefixMode == 0:
            if token == '@prefix':
                prefixMode = 1
            else:
                if qName.match(token):
                    n = token.find(':')
                    prefix = token[:n]
                    if prefix == '_' and '_' not in prefixMap:
                        yield token
                    else:
                        yield '<' + prefixMap[prefix] + token[n+1:] + '>'
                elif uri.match(token):
                    yield '<' + absolutize(token[1:-1], baseURI) + '>'
                else:
                    yield token
            
        elif prefixMode == 1:
            if not qName.match(token):
                raise ValueError('Expected: qName')
            prefixMode = token[0:token.find(':')]
        elif prefixMode == 2:
            if token != '.':
                raise ValueError('Expected: "." ')
            prefixMode = 0
        else:
            if not uri.match(token):
                raise ValueError('Expected: uri')
            prefixMap[prefixMode] = absolutize(token[1:-1], baseURI)
            if fn:
                fn(prefixMode, absolutize(token[1:-1], baseURI))
            prefixMode = 2

#if __name__ == '__main__':
#    import sys
#    dekeywordize(sys.stdin, sys.stdout)
