"""

Try to make a nice HTML page for this KB

given our html.py, we could build this from a stream, I think!

"""
__version__ = "$Revision$"
# $Id$

from html import *
import LX
import cStringIO
import re

class Entry:

    def __init__(self, term):
        self.term = term
        self.label = None
        self.asSubject = []
        self.asPredicate = []
        self.asObject = []
        self.id = None
        self.tag = None
        

class Serializer:

    def __init__(self, stream, flags=""):
        # LX.language.abstract.Serializer.__init__(self)
        self.stream = stream
        # no flags right now... 
        self.d = Document()
        self.d.head.append(stylelink("htables.css"))
        self.d.append(p("formatted by cwm", attrs={"id":"__form"}))

    def makeComment(self, comment):
        self.d.append(Comment(comment))
        
    def serializeKB(self, kb):
        d=self.d
        d.head.append(title("KB Dump [ Not Implemented ]"))

        # flatten

        # oh, I just want the triples....

        scope = {
            ("legal",): re.compile(r"^[a-zA-Z0-9_]+$"),
            ("hint",): re.compile(r"(?:\/|#)([a-zA-Z0-9_]*)/?$"),
            }

        entry = { }
        idCount=1
        for t in kb:
            assert t.function == LX.fol.RDF
            for term in t.args:
                if not entry.has_key(term):
                    e = Entry(term)
                    e.label = term.getNameInScope(scope)
                    # interpretations?
                    e.id = "_id"+str(idCount)
                    idCount+=1
                    e.tag = a(e.label, "#"+e.id)
                    entry[term] = e
            entry[t.args[0]].asSubject.append(t)
            entry[t.args[1]].asPredicate.append(t)
            entry[t.args[2]].asObject.append(t)

        entries = entry.values()
        entries.sort(lambda a, b: cmp(a.label, b.label))

        p1 = p("Terms used: ")
        d.append(p1)
        for e in entries:
            p1.append(e.tag)
            p1.append(" ")

        for e in entries:
            section = div([], attrs={'id':e.id})
            section.append(h1(e.label))
            try:
                interps = kb.interpretation[e.term]
                uri = interps[0]
                link = a(uri, uri)
                section.append(p(["URI: ", link]))
            except KeyError:
                pass

            if 0:
                table=Element("table")
                for t in e.asSubject:
                    row=tr([td(["has ", entry[t.args[1]].tag]   ),
                            td(  entry[t.args[2]].tag   )])
                    table.append(row)
                for t in e.asObject:
                    row=tr([td(["is ", entry[t.args[1]].tag, " of"]),
                            td(  entry[t.args[0]].tag   )])
                    table.append(row)
            else:
                left = None
                middle = h1(e.label)
                right = None

                if e.asSubject:
                    right = htable()
                    for t in e.asSubject:
                        row=tr([td([" >- ", entry[t.args[1]].tag, " -> "]   ),
                                td(  entry[t.args[2]].tag   )])
                        right.append(row)
                else:
                    right = h1("*")

                if e.asObject:
                    left = htable()
                    for t in e.asObject:
                        row=tr([td(  entry[t.args[0]].tag   ),
                                td([" >- ", entry[t.args[1]].tag, " -> "]),])
                        left.append(row)
                else:
                    left = h1("*")

                table=htable(attrs={'border':'5', 'width':'100%'})
                table.append(tr([td(left, attrs={'width':'40%'}), td(middle, attrs={'valign':'top'}), td(right, attrs={'width':'40%'})]))

            section.append(table)

            d.append(section)

##         i = 0
##         for key in terms.keys():
##             print i, #key, 
##             try:
##                 interp = kb.interpretation[key][0]
##                 print `interp`
##             except KeyError:
##                 print "-"
##             i+=1
                
        d.writeTo(self.stream)

#defaultSerializer = Serializer()

#def serialize(x):
#    return defaultSerializer.serialize(x)

def test():
    s = Serializer()
    
if __name__ =='__main__':
    test()

# $Log$
# Revision 1.2  2003-02-01 05:58:12  sandro
# intermediate lbase support; getting there but buggy; commented out some fol chreccks
#
# Revision 1.1  2003/01/29 20:18:28  sandro
# Added scaffolding for --language=htables (etc) to route through lxkb
#

