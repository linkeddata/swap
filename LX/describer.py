"""Support classes for Describers (which convert native knowledge into
LX sentences).

"""
__version__ = "$Revision$"
# $Id$

import LX

class DescriptionFailed(Exception):
    pass

class ListDescriber:
    "A describer of python sequences using rdf:first/rest/nil"

    def describe(object, ladder):
        try:
            if len(object) == 0:
                if ladder.missing("term"):
                    raise (DescriptionFailed,
                           'Cannot describe empty list with a given term')
                else:
                    return LX.rdfns.nil
            if ladder.has("term"):
                term = ladder.term
            else:
                term = ladder.kb.newExistential()
            if ladder.missing("term"): term = ladder.kb.newExistential()
            kb.add(Triple(term, LX.rdfns.first,
                          describer.describe(t[0], kb, describer=describer,
                                             ladder=ladder)))
            kb.add(Triple(term, LX.rdfns.rest,
                          describer.describe(t[1:], kb, describer=describer,
                                             ladder=ladder)))
            return term
        except TypeError:
            raise DescriptionFailed, 'not a list'

class CombinedDescriber:

    def __init__(describers):
        self.describers = describers[:]

    def describe(self, ladder):
        ladder = ladder.setIfMissing("describer", self)
        for describer in self.describers:
            try:
                result = describer.describe(object, ladder)
                if result: return result
            except DescriptionFailed:
                pass
        raise DescriptionFailed, 'all describers failed'


# $Log$
# Revision 1.1  2002-08-29 11:00:46  sandro
# initial version, mostly written or heavily rewritten over the past
# week (not thoroughly tested)
#

 
