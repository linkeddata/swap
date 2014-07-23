"""
  Copyright (c) 2006 Jan-Klaas Kollhof

  This file is part of jsonrpc.

  jsonrpc is free software; you can redistribute it and/or modify
  it under the terms of the GNU Lesser General Public License as published by
  the Free Software Foundation; either version 2.1 of the License, or
  (at your option) any later version.

  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public License
  along with this software; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA 
"""


        
class PeerObjectProxy(object):
    """creates a peer object which will send requests to the remote service when invoked."""
    def __init__(self, name, conn):
        self._name = name
        self._conn = conn
    
    def notify(self, *args):
        self._conn.sendNotify(self._name, args)
        
    def __call__(self, *args):
        evt  = self._conn.sendRequest(self._name, args)
        return evt.waitForResponse()

    def __getattr__(self, name):
        return PeerObjectProxy(self._name + "." + name, self._conn)


class PeerProxy:
    def __init__(self, connectionHandler):
        self._connectionHandler = connectionHandler
    
    def __getattr__(self, name):
        return PeerObjectProxy(name, self._connectionHandler)


import re


class ServiceProxy(PeerProxy):
    def __init__(self, url, localService=None, messageDelimiter=""):
        m = re.match(r"^jsonrpc:\/\/(.*):(\d*)$", url)
        if m:
            from jsonrpc.socketserver import SocketServiceHandler
            import socket
            from threading import Thread
            
            (host, port)= m.groups()
            port = int(port)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            conn = SocketServiceHandler(s, localService,messageDelimiter=messageDelimiter)
            PeerProxy.__init__(self, conn)
            
            t=Thread(target=conn.receiveForever)
            t.setDaemon(True)
            t.start()
        else:
            from jsonrpc.http import HTTPClientConnectionHandler
            conn= HTTPClientConnectionHandler(url, localService,messageDelimiter=messageDelimiter)
            PeerProxy.__init__(self, conn)

    


