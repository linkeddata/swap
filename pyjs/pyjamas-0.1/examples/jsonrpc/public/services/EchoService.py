#!/usr/bin/env python2.4

class Service:
    def echo(self, msg):
        return msg

from jsonrpc.cgihandler import handleCGIRequest

handleCGIRequest(Service())
