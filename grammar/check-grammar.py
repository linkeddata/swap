#! /usr/bin/python
# Check ambiguity as for predictive parser
#
import llyn
from myStore import load, Namespace
from term import Literal
import diag
diag.chatty_flag=10

from sys import argv, exit, stderr
from time import clock
import re




branchTable = {}
tokenRegexps = {}

def recordError(str):
    global errors
    errors.append(str)
    str2 =  "##### ERROR:  " + str
    return str2

def deColonise(s):
    t = ""
    for ch in s:
	if ch == ":": ch = "_"
	t = t + ch
    return t

def toYacc(x, tokenRegexps):
    if isinstance(x, Literal):
	return "'" + str(x.value()) + "'"  # @@@ Escaping
    if x in tokenRegexps:
	return deColonise(`x`).upper()
    return deColonise(`x`)

	
def yaccConvert(yacc, top, tokenRegexps):
    global already, agenda, errors
    already = []
    agenda = []
    errors = []
    for x in tokenRegexps:
	yacc.write("%%token %s\n" % toYacc(x, tokenRegexps))
    yacc.write("\n")
    yacc.write("%%\n")
    yaccProduction(yacc, top, tokenRegexps)
    while agenda:
	x = agenda[0]
	agenda = agenda[1:]
	already.append(x)
	yaccProduction(yacc, x, tokenRegexps)
    yacc.write("eof:  /* empty */; \n")
    yacc.write("%%\n")
    
def yaccProduction(yacc, lhs,  tokenRegexps):
    if lhs is BNF.void:
	print "\nvoid"
	return
    if lhs is BNF.eof:
	print "\nEOF"
	return
    if isinstance(lhs, Literal):
	literalTerminals[lhs.value()] = 1
#    	print "\nLiteral %s" %(lhs)
	return

    rhs = g.the(pred=BNF.matches, subj=lhs)
    if rhs != None:
	print "\nToken %s matches regexp %s" %(lhs, rhs)
#	tokenRegexps[lhs] = re.compile(rhs.value())
	return
    rhs = g.the(pred=BNF.mustBeOneSequence, subj=lhs)
    if rhs == None:
	print recordError("No definition of " + `lhs`)
	raise ValueError("No definition of %s  in\n %s" %(`lhs`, `g`))
    options = rhs
    print "\nProduction %s :: %s  ie %s" %(`lhs`, `options` , `options.value()`)
    yacc.write("\n%s:" % toYacc(lhs, tokenRegexps))

    branches = g.each(subj=lhs, pred=BNF.branch)
    first = 1
    for branch in branches:
	if not first:
	    yacc.write("\t|\t")
	first = 0
	option = g.the(subj=branch, pred=BNF.sequence)
	print "\toption: "+`option.value()`
	yacc.write("\t")
	if option.value() == [] and yacc: yacc.write(" /* empty */")
	for part in option:
	    if part not in already and part not in agenda: agenda.append(part)
	    yacc.write(" %s" % toYacc(part, tokenRegexps))
	yacc.write("\n")
    yacc.write("\t;\n")
	
########################################## end of yacc converter

literalTerminals = {}
def doProduction(lhs):
    global branchTable
    if lhs is BNF.void:
	print "\nvoid"
	return
    if lhs is BNF.eof:
	print "\nEOF"
	return
    if isinstance(lhs, Literal):
	literalTerminals[lhs.value()] = 1
#    	print "\nLiteral %s" %(lhs)
	return

    branchDict = {}

    rhs = g.the(pred=BNF.matches, subj=lhs)
    if rhs != None:
	print "\nToken %s matches regexp %s" %(lhs, rhs)
	tokenRegexps[lhs] = re.compile(rhs.value())
	cc = g.each(subj=lhs, pred=BNF.canStartWith)
	if cc == []: print recordError("No recod of what token %s can start with" % `lhs`)
	print "\tCan start with: %s" % cc 
	return
    rhs = g.the(pred=BNF.mustBeOneSequence, subj=lhs)
    if rhs == None:
	print recordError("No definition of " + `lhs`)
	return
#	raise RuntimeError("No definition of %s  in\n %s" %(`lhs`, `g`))
    options = rhs
    print "\nProduction %s :: %s  ie %s" %(`lhs`, `options` , `options.value()`)
    succ = g.each(subj=lhs, pred=BNF.canPrecede)
    print "\tCan precede ", succ

    branches = g.each(subj=lhs, pred=BNF.branch)
    for branch in branches:
	option = g.the(subj=branch, pred=BNF.sequence)
	print "\toption: "+`option.value()`
	for part in option:
	    if part not in already and part not in agenda: agenda.append(part)
	    y = `part`
	conditions = g.each(subj=branch, pred=BNF.condition)
	if conditions == []:
	    print recordError(" NO SELECTOR for %s option %s ie %s" %(`lhs`, `option`, `option.value()` ))
	    if option.value == []: # Void case - the tricky one
		succ = g.each(subj=lhs, pred=BNF.canPrecede)
		for y in succ:
		    print "\t\t\tCan precede ", `y`
	print "\t\tConditions: %s" %(conditions)
	for str1 in conditions:
	    if str1 in branchDict:
		print recordError("Conflict: %s is also the condition for %s" % (
				str1, branchDict[str1].value()))
	    branchDict[str1.__str__()] = option
#	    break

    for str1 in branchDict:
	for str2 in branchDict:
	    
	    s1 = str1.__str__()
	    s2 = str2.__str__()
# @@ check that selectors are distinct, not substrings
	    if (s1.startswith(s2) or s2.startswith(s1)) and branchDict[str1] is not branchDict[str2]:
		print "WARNING: for %s, %s indicates %s, but  %s indicates %s" % (
			    lhs, s1, branchDict[str1], s2, branchDict[str2])
#		print recordError("Conflict: for %s, %s indicates %s, but  %s indicates %s" % (
#			    option.value(), s1, branchDict[str1], s2, branchDict[str2]))
    branchTable[lhs] = branchDict


######################### Parser based on the RDF Context-free grammar

whiteSpace = re.compile(r'[ \t]*((#[^\n]*)?\r?\n)?')
singleCharacterSelectors = "\t\r\n !\"#$%&'()*.,+/;<=>?[\\]^`{|}~"
notQNameChars = singleCharacterSelectors + "@"  # Assume anything else valid qname :-/
notNameChars = notQNameChars + ":"  # Assume anything else valid name :-/
#quotedString = re.compile(r'"([^\n"\\]|(\\[\\"a-z]))*"')   # @@@ Missing: \U escapes etc
quotedString = re.compile(r'"[^\n"\\]+"')   # @@@ Missing: \U escapes etc"
tripleQuotedString = re.compile(r'""".*"""')	# @@@ Missing: any control on the content.

class PredictiveParser:
    "A parser for N3 or derived languages"

    def __init__(parser, sink, top,  branchTable, tokenRegexps):
	parser.sink = sink
	parser.top = top    #  Initial production for whole document
	parser.branchTable = branchTable
	parser.tokenRegexps = tokenRegexps
	parser.lineNumber = 1
	parser.keywords = [ "a", "is", "of", "this" ]
	parser.verb = 0  # Verbosity
	
    def token(parser, str, i):
	"The Tokenizer: Returns (token type, start of token)"
    
	while 1:
	    m = whiteSpace.match(str, i)
	    if m == None or m.end() == i: break
	    parser.lineNumber += str[i: m.end()].count("\n")
	    i = m.end()
	if i == len(str):
	    return "",  i # eof
	
	if parser.verb: print "%i) Looking at:  ...%s$%s..." % (
	    parser.lineNumber, str[i-10:i],str[i:i+10])
	for double in "=>", "<=", "^^":
	    if double == str[i:i+2]: return double, i
    
	ch = str[i]
	if ch in singleCharacterSelectors:
	    return ch, i
	if ch in "+-0123456789":
	    return "0", i #  Numeric
	j = i+1
	if ch == "@":
	    while str[j] not in notNameChars: j = j + 1
	    if str[i+1:j] == "keywords" : parser.keywords = [] # Special
	    return str[i:j], i # keyword
    
	while str[j] not in notQNameChars: j = j+1
	word = str[i:j]
	if word in parser.keywords:
	    if word == "keywords" : parser.keywords = []	# Special
	    return "@" + word, i  # implicit keyword
	return "a", i    # qname, langcode, or barename

    def around(parser, str, this):
	"The line around the given point"
	sol = str.rfind("\n", this)
	if sol <= 0: sol = 0
	eol = str.find("\n", this)
	if eol <= 0: eol = len(str)
	return "On line %i at $ in: %s$%s" %(parser.lineNumber, str[sol:this], str[this:eol])
	
    def parse(parser, str):
	tok, this = parser.token(str, 0)
	return parser.parseProduction(parser.top, str, tok, this)
	
    def parseProduction(parser, lhs, str, tok=None, this=0):
	"The parser itself."

	if tok == "": return tok, this # EOF    
	lookupTable = parser.branchTable[lhs]
	rhs = lookupTable.get(tok, None)  # Predict branch from token
	if rhs == None: raise SyntaxError(
		"Found %s when expecting some form of %s,\n\tsuch as %s\n\t%s"
		    %(tok, lhs, lookupTable.keys(), parser.around(str, this)))
	print "%i  %s means expand %s as %s" %(parser.lineNumber,tok, lhs, rhs.value())
	for term in rhs:
	    if isinstance(term, Literal):
		lit = term.value()
		next = this + len(lit)
		if str[this:next] == lit: pass
		elif "@"+str[this:next-1] == lit: next = next-1
		else: raise SyntaxError(
		    "Found %s where %s expected\n\t %s" %
			(str[this:next], lit, parser.around(str, this)))
	    else:
		rexp = tokenRegexps.get(term, None)
		if rexp == None: # Not token
		    tok, this = parser.parseProduction(term, str, tok, this)
		    continue
		m = rexp.match(str, this)
		if m == None:
		    raise SyntaxError("Token: should match %s\n\t" % 
				(rexp.pattern, parser.around(str, this)))
		next = m.end()
	    tok, this = parser.token(str, next)  # Next token
	return tok, this

############################### Test Program

# The Grammar formula

print "Loading", argv[1]
start = clock()
g = load(argv[1])
taken = clock() - start
print "Loaded %i statements in %fs, ie %f/s." % (len(g), taken, len(g)/taken)

document = g.newSymbol(argv[2])

BNF = Namespace("http://www.w3.org/2000/10/swap/grammar/bnf#")
#RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

already = []
agenda = []
errors = []
doProduction(document)
while agenda:
    x = agenda[0]
    agenda = agenda[1:]
    already.append(x)
    doProduction(x)
    
if errors != []:
    print "###### FAILED with %i errors." % len(errors)
    for s in errors: print "\t%s" % s
    exit(-2)
else:
    print "Ok for predictive parsing"

#print "Branch table:", branchTable
print "Literal terminals:", literalTerminals.keys()
print "Token regular expressions:"
for r in tokenRegexps: print "\t%s matches %s" %(r, tokenRegexps[r].pattern) 

yacc=open(argv[1]+"-yacc.y", "w")
yaccConvert(yacc, document, tokenRegexps)
#while agenda:
#    x = agenda[0]
#    agenda = agenda[1:]
#    already.append(x)
#    yaccProduction(yacc, x, tokenRegexps)
yacc.close()

if len(argv) <= 3: exit(0)
parseFile = argv[3]
ip = open(parseFile)
str = ip.read()
sink = g.newFormula()
p = PredictiveParser(sink=sink, top=document, branchTable= branchTable,
	tokenRegexps= tokenRegexps)
p.parse(str)

    
#ends
