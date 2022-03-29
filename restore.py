#! /usr/bin/python
"""


Copyright ()  2015 World Wide Web Consortium, (Massachusetts Institute
of Technology, European Research Consortium for Informatics and Mathematics,
Keio University). All Rights Reserved. This work is distributed under the
W3C Software License [1] in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 FOR A PARTICULAR PURPOSE.
"""


from __future__ import generators
# see http://www.amk.ca/python/2.2/index.html#SECTION000500000000000000000

from swap import IndexedFormula, Formula, Namespace


class RestorerFormula(Formula):
    """A formula which accepts an N3 dump of a store and from it
    loads restores a store from a previous (or initial) state.

    In other words, load stuff like like
         <doc1> log:semantics { <foo> <p> 123 } .
         <doc2> log:semantics { <bar> <pq> 567 } .
    as though the various documents had been loaded themselves whith that data.
    Work in progress.
    """

    def __init__(self, store):
        self.store = store

    def add(self, subj, pred, obj, why = None):
        """Add a triple to tghe metaformula, which directs
        where data is to be loaed in the store"""

        log = Namespace('http://www.w3.org/2000/10/swap/log#')
        if pred.sameTerm(log.('semantics')):
