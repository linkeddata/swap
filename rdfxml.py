#! /usr/bin/python
"""
    A module to allow one to chose which RDF parser to use.
    This is not done correctly, so I don't expect this file
    to last very long.

    $ID   $

"""

def rdfxmlparser(store, openFormula, thisDoc=None,  flags="", why=None, parser='sax2rdf'):
    if parser == 'rdflib':
        import rdflib_user
        return rdflib_user.rdflib_handoff(store, openFormula,thisDoc, why=why) #put something here
    else:   # parser == sax2xml
        import sax2rdf
        return  sax2rdf.RDFXMLParser(store, openFormula,  thisDoc=thisDoc, flags=flags, why=why)
