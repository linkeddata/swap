#  Python

import llyn
from myStore import load, Namespace
from thing import Literal
import diag
diag.chatty_flag=10

from sys import argv


already = []
agenda = []

def doProduction(lhs):
    if lhs is BNF.void:
	print "void"
	return
    if type(lhs) is type (u""):
	print "Token %s" %(lhs)
	return
    rhs = g.the(pred=BNF.matches, subj=lhs)
    if rhs != None:
	print "Token %s matches regexp %s" %(lhs, rhs)
	return
    rhs = g.the(pred=BNF.mustBeOneSequence, subj=lhs)
    if rhs == None:
	print "############## NO DEFINITION OF ", `lhs`
	return
	raise RuntimeError("No definition of %s  in\n %s" %(`lhs`, `g`))
    options = rhs.value()
    print "Production %s :: %s" %(`lhs`, `options` )
    selectors = g.each(subj=lhs, pred=BNF.selector)
    print "Selectors:", selectors
    for option in options:
	print "  Option "+`option`
	for part in option:
#	    print "    Part: " + `part`
	    if part not in already and part not in agenda: agenda.append(part)
	for sel in selectors:
	    str, branch = sel.value()
	    print "Selector %s for %s" %(str, branch)
	    if branch == rhs:
		print "**** Selector %s for option %s" %(str, `branch`)
    



# The Grammar formula
grammar = argv[1]
print "Loading", grammar
g = load(grammar)
print "Loaded."

    
N3 = Namespace("http://www.w3.org/2000/10/swap/grammar/n3#")
BNF = Namespace("http://www.w3.org/2000/10/swap/grammar/bnf#")
RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#")

document = N3.n3document

doProduction(document)
while agenda:
    x = agenda[0]
    agenda = agenda[1:]
    already.append(x)
    doProduction(x)
    

#ends
