#  Python

import llyn
from myStore import load, Namespace
from term import Literal
import diag
diag.chatty_flag=10

from sys import argv


already = []
agenda = []

dict = {}

def doProduction(lhs):
    if lhs is BNF.void:
	print "\nvoid"
	return
    if lhs is BNF.eof:
	print "\nEOF"
	return

    if isinstance(lhs, Literal):
#    	print "\nLiteral %s" %(lhs)
	return

    branchDict = {}
    dict[lhs] = branchDict

    rhs = g.the(pred=BNF.matches, subj=lhs)
    if rhs != None:
	print "Token %s matches regexp %s" %(lhs, rhs)
	return
    rhs = g.the(pred=BNF.mustBeOneSequence, subj=lhs)
    if rhs == None:
	print "############## NO DEFINITION OF ", `lhs`
	return
	raise RuntimeError("No definition of %s  in\n %s" %(`lhs`, `g`))
    options = rhs
    print "\nProduction %s :: %s  ie %s" %(`lhs`, `options` , `options.value()`)

    succ = g.each(subj=lhs, pred=BNF.canPrecede)
    print "\tCan precede ", succ

    branches = g.each(subj=lhs, pred=BNF.branch)
#    print "branches:", `branches`
    for branch in branches:
	option = g.the(subj=branch, pred=BNF.sequence)
	print "\toption: "+`option.value()`
	for part in option:
#	    print "    Part: " + `part`
	    if part not in already and part not in agenda: agenda.append(part)
	conditions = g.each(subj=branch, pred=BNF.condition)
	if conditions == []:
	    print "\t\t####### NO SELECTOR for %s option %s ie %s" %(`lhs`, `option`, `option.value()` )
	    if option.value == []: # Void case - the tricky one
		succ = g.each(subj=lhs, pred=BNF.canPrecede)
		for y in succ:
		    print "\t\t\tCan precede ", `y`
	for str1 in conditions:
	    print "\t\tCondition '%s'" %(str1)
	    if str1 in branchDict:
		print "##### Conflict: %s is also the condition for %s" % (
				str1, branchDict[str1].value())
	    branchDict[str1] = rhs
	    break
	for str1 in branchDict:
	    for str2 in branchDict:
		
		s1 = str1.__str__()
		s2 = str2.__str__()
		if s1.startswith(s2) and branchDict[str1] is not branchDict[str2]:
		    print "\t\t##### Conflict: %s ans %s are conditions is also the condition for %s" % (
				s1, s2, `option.value()`)

# @@ check that selectors are distinct, not substrings


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
