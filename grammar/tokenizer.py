"""keywordizer

    Extremely simple --- will divide a file into tokens based on regexps
"""


import re

def group(n): 
    return '(%s)' % '|'.join(['(' + w + ')' for w in n])

def tokenizeFile(inFile, singleChars, whiteSpace, regexps):
    string = inFile.read()
    return tokenize(string, singleChars, whiteSpace, regexps)

def tokenize(string, singleChars, whiteSpace, regexps):
#    string = inFile.read()
#    regexp = re.compile(group(regexps))
    i = 0
    while i <= len(string):
        while string[i:i+1] in whiteSpace:
            i = i+1
            if i >= len(string):
                break
        if i >= len(string):
            break
        if string[i] in singleChars:
            #print string[i]
            yield string[i]
            i = i+1
        else:
            j = i
            for regexp in regexps:
                m = regexp.match(string, i)
                if m is None:
                    if string[i] == '@':
                        m = regexp.match(string, i+1)
                        if m is None:
                            continue
                    else:
                        continue
                k = m.end()
                if k>j: j = k
            if j>i:
                #print string[i:j]
                yield string[i:j]
                i = j
            else:
                raise ValueError('I didn\'t match! %s' % `string[i:i+10]`)
                
                


def deleteme(x):
    print `x`
    return re.compile(x, re.S+re.U)

def testharness():
    import sys
    import dekeywordizer
    import deprefixizer
    explicitURI = "<[^>]*>"
    comment     = '#[^\\n]*'
    numericLiteral = """[-+]?[0-9]+(\\.[0-9]+)?(e[-+]?[0-9]+)?"""
    bareNameChar = "[a-zA-Z_][a-zA-Z0-9_]"
    bareName    = "[a-zA-Z_][a-zA-Z0-9_]*"  #This is totally wrong
    bareNameOnly = bareName + '$'
    qName = "(" + bareName + ")?:(" + bareName + ")?"
    variable    = '\\?' + bareName
    langcode    = "[a-z]+(-[a-z0-9]+)*"
    string      = "(\"\"\"[^\"\\\\]*(?:(?:\\\\.|\"(?!\"\"))[^\"\\\\]*)*\"\"\")|(\"[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*\")"
    equals	= "="
    implies	= "=>"
    backwards_implies = "<="
    carrot	= "\\^"
    double_carrot = "\\^\\^"
    singleChars = ';,.()[]{}!'
    whiteSpace  = ' \t\n'
    argList = [numericLiteral, explicitURI, comment, bareName, qName, variable, langcode, \
               string, equals, implies, backwards_implies, carrot, double_carrot]
    realArgList = [deleteme(x) for x in argList]
    z = tokenize(file(sys.argv[1]), singleChars, whiteSpace, realArgList)
    y = dekeywordizer.dekeywordize(z, re.compile(bareNameOnly, re.S+re.U))
    prefixMap = {}
    return deprefixizer.deprefixize(y, prefixMap,
                                    re.compile(qName, re.S+re.U),
                                    re.compile(explicitURI, re.S+re.U))

if __name__ == '__main__':
    print [a for a in testharness()]
