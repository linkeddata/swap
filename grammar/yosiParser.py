"""An n3 parser, to replace 


"""
import sys
import re

import dekeywordizer
import deprefixizer
import tokenizer
#import triple_maker
import toXML
import notation3
import diag

from RDFSink import RDF_type_URI, RDF_NS_URI, DAML_sameAs_URI, parsesTo_URI
from RDFSink import RDF_spec, List_NS, uniqueURI

LOG_implies_URI = "http://www.w3.org/2000/10/swap/log#implies"

INTEGER_DATATYPE = "http://www.w3.org/2001/XMLSchema#integer"
FLOAT_DATATYPE = "http://www.w3.org/2001/XMLSchema#double"
DECIMAL_DATATYPE = "http://www.w3.org/2001/XMLSchema#decimal"

explicitURI = re.compile("<[^>]*>", re.S+re.U)
comment     = re.compile('#[^\\n]*', re.S+re.U)
numericLiteral = re.compile("""([-+]?[0-9]+)(\\.[0-9]+)?(e[-+]?[0-9]+)?""", re.S+re.U)
bareNameChar = re.compile("[a-zA-Z_][a-zA-Z0-9_]", re.S+re.U)
bareName    = "[a-zA-Z_][a-zA-Z0-9_\\-]*"  #This is totally wrong
bareNameOnly = re.compile(bareName + '$', re.S+re.U)
qName = re.compile("(" + bareName + ")?:(" + bareName + ")?", re.S+re.U)
variable    = re.compile('\\?' + bareName, re.S+re.U)
bareName    = re.compile(bareName, re.S+re.U)
langcode    = re.compile("[a-z]+(-[a-z0-9]+)*", re.S+re.U)
string      = re.compile("(\"\"\"[^\"\\\\]*(?:(?:\\\\.|\"(?!\"\"))[^\"\\\\]*)*\"\"\")|(\"[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*\")", re.S+re.U)
equals	= re.compile("=", re.S+re.U)
implies	= re.compile("=>", re.S+re.U)
backwards_implies = re.compile("<=", re.S+re.U)
carrot	= re.compile("\\^", re.S+re.U)
double_carrot = re.compile("\\^\\^", re.S+re.U)
singleChars = ';,.()[]{}!'
whiteSpace  = ' \t\n\r'
realArgList = [numericLiteral, explicitURI, comment, bareName, qName, variable, langcode, \
               string, equals, implies, backwards_implies, carrot, double_carrot]
#realArgList = [re.compile(x, re.S+re.U) for x in argList]

class SinkParser:
    def __init__(self, store, openFormula=None, thisDoc="", baseURI=None,
                 genPrefix = "", metaURI=None, flags="",
                 why=None):

    	self._bindings = {}
        if thisDoc != "":
	    assert ':' in thisDoc, "Document URI if any must be absolute: <%s>" % thisDoc
	    self._bindings[""] = thisDoc + "#"  # default


        self._store = store
	if genPrefix: store.setGenPrefix(genPrefix) # pass it on
	
	self._thisDoc = thisDoc
        self.lines = 0              # for error handling
	self.startOfLine = 0	    # For calculating character number
        self._genPrefix = genPrefix
	self.keywordsSet = 0    # When and only when they have been set can others be considerd qnames	self._reason = why	# Why the parser w
	self._reason2 = None	# Why these triples
	if diag.tracking: self._reason2 = BecauseOfData(store.newSymbol(thisDoc), because=self._reason) 

        if baseURI: self._baseURI = baseURI
        else:
	    if thisDoc:
		self._baseURI = thisDoc
	    else:
		self._baseURI = ""

        assert not self._baseURI or ':' in self._baseURI

        if not self._genPrefix:
	    if self._thisDoc: self._genPrefix = self._thisDoc + "#_g"
	    else: self._genPrefix = uniqueURI()

	if openFormula ==None:
	    if self._thisDoc:
		self._formula = store.newFormula(thisDoc + "#_formula")
	    else:
		self._formula = store.newFormula()
	else:
	    self._formula = openFormula
	import sys
	#self._tripleMaker = toXML.tmToRDF(sys.stdout, "foo:", base="file:/home/syosi/CVS-local/WWW/2000/10/swap/test/")#triple_maker.TripleMaker(self._formula)
        self._tripleMaker = notation3.tmToN3(sys.stdout.write, genPrefix="foo:", base="file:/home/syosi/CVS-local/WWW/2000/10/swap/test/")
	self._bindings[''] =  self._baseURI + '#'

    def startDoc(self):
        self._tripleMaker.start()

    def endDoc(self):
        return self._tripleMaker.end()


    def feed(self, octets):
        string = octets.decode('utf_8')
        z = tokenizer.tokenize(string, singleChars, whiteSpace, realArgList)
        y = dekeywordizer.dekeywordize(z, bareNameOnly)
        x = deprefixizer.deprefixize(y, self._baseURI, self._bindings,
                                    qName,
                                    explicitURI,
                                    self._tripleMaker.bind)
        self._parse(x)
#        for prefix, uri in self._bindings.items():
#            self._tripleMaker.bind(prefix,uri)

    def _parse(self, x):
        tm = self._tripleMaker
        bNodes = {}
        nextBNode = 0
        forMode = 0
        prevString = 0
        for token in x:
            if prevString == 2:
                prevString = 1
            if forMode == 0:
                if token == '.':
                    try:
                        tm.endStatement()
                    except ValueError:
                        tm.forewardPath()
                elif token == ';':
                    tm.endStatement()
                    tm.addNode(None)
                elif token == ',':
                    tm.endStatement()
                    tm.addNode(None)
                    tm.addNode(None)
                elif token == '=>':
                    tm.addSymbol(LOG_implies_URI)

                elif token == '<=':
                    tm.IsOf()
                    tm.addSymbol(LOG_implies_URI)
                elif token == '=':
                    tm.addSymbol(DAML_sameAs_URI)
                elif token == '@forAll':
                    forMode = 1
                elif token == '@forSome':
                    forMode = 2
                elif token == '@a':
                    tm.addSymbol(RDF_type_URI)
                elif token == '@is':
                    tm.IsOf()
                elif token == '@of':
                    assert tm.checkIsOf()
                elif token == '{':
                    tm.beginFormula()
                elif token == '}':
                    tm.endFormula()
                elif token == '[':
                    tm.beginAnonymous()
                elif token == ']':
                    tm.endAnonymous()
                elif token == '(':
                    tm.beginList()
                elif token == ')':
                    tm.endList()
                elif token == '@has':
                    pass
                elif token == '@this':
                    tm.addNode('@this')
                elif token == '^':
                    tm.backwardPath()
                elif token == '!':
                    tm.forewardPath()
                elif explicitURI.match(token):
                    tm.addSymbol(token[1:-1])
                elif numericLiteral.match(token):
                    m = numericLiteral.match(token)
                    if '.' not in token:
                        tm.addLiteral(long(token))
                    elif m is None:
                        raise ValueError("How exactly did I get here?")
                    elif m.groups(3) is not None:
                        tm.addLiteral(float(token))
                    elif m.groups(2) is not None:
                        tm.addLiteral(float(token))
                    else:
                        tm.addLiteral(long(token))
                elif string.match(token):
                    if token[0:3] == '"""':
                        a = 3
                    else:
                        a = 1
                    tm.addLiteral(token[a:-a])
                elif variable.match(token):
                    tm.addQuestionMarkedSymbol(self._baseURI + '#' + token[1:])
                elif token[:2] == '_:':
                    tm.addAnonymous(token)
        
                else:
                    raise ValueError(token)
            elif forMode == 1:
                if explicitURI.match(token):
                    tm.declareUniversal(token[1:-1])
                else:
                    raise ValueError(token)
                forMode = 3
            elif forMode == 2:
                if explicitURI.match(token):
                    tm.declareExistential(token[1:-1])
                else:
                    raise ValueError(token)
                forMode = 4               
            elif forMode == 3 or forMode == 4:
                if token == '.':
                    forMode = 0
                elif token == ',':
                    forMode = forMode - 2
                else:
                    raise ValueError(token)
                
