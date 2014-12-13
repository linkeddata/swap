#
from xml.dom.minidom import parse, Text
from diag import verbosity, setVerbosity, progress
import thing, llyn

kb=thing.formula()
setVerbosity(99)


def do(ele, level=0):
    if isinstance(ele, Text):
	if verbosity() > 70: progress("Ignoring text '%s'" % ele.nodeValue)
	return None
    ln = ele.localName
    if verbosity() > 20: progress("  "*level, ln)
    if ln == "dict":
	me = kb.newBlankNode()
	n = len(ele.childNodes)
	i = 0
	pred = None
	while i<n:
	    e = ele.childNodes[i]
	    if isinstance(e, Text):
		if verbosity() > 70: progress("Ignoring text '%s'" % e.nodeValue)
		i = i + 1
		continue
	    if e.localName == "key":
		property = e.firstChild.data
		if not property: property = "nullProp"
		pred = kb.newSymbol(property)
	    else:
		value = ele.childNodes [i]
		obj = do(value, level+1)
		kb.add(me, pred, obj)
	    i = i + 1
	return me
    elif ln == "string":
	s = ele.firstChild.data
	return kb.literal(s)
    elif ln == "array":
	a = []
	for e in ele.childNodes:
	    a.append(do(e))
	a.reverse()
	last = kb.store.nil
	for item in a:
	    x = kb.newBlankNode()
	    kb.add(x, kb.store.first, kb.newSymbol(item))
	    kb.add(x, kb.store.rest, last)
	    last = x
	return last
    else:
	raise RuntimeError("Unexpected tag %s" % ln)
	
doc = parse("/dev/stdin")
e = doc.documentElement
for x in e.childNodes:
    do (x)
    
