#!/usr/bin/env python
"""
Wrap llyn.py as plwm components.   Could go into llyn.py
but I don't want to muck with that right now.

"""

import pluggable
import llyn

class Store(pluggable.Store, llyn.RDFStore):

    def __init__(self, host=None, copyFrom=None):
        if copyFrom is not None:
            raise RuntimeError, "Not implemented"
        if host is not None: self.host = host
        apply(llyn.RDFStore.__init__, [self])
