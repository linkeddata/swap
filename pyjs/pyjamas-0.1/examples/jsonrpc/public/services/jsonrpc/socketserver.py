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
from jsonrpc import SimpleServiceHandler
import socket

from threading import Thread
    
    
class SocketServiceHandler(SimpleServiceHandler):
    def __init__(self, socket, service, messageDelimiter=""):
        self.socket = socket
        SimpleServiceHandler.__init__(self, service, messageDelimiter=messageDelimiter)
        
    def receiveForever(self):
        while 1:
            try:
                data = self.socket.recv(1024)
            except:
                data = None

            if not data:
                if self.socket:
                    self.close()
                return
            else:
                self.handlePartialData(data)
            
    def send(self, data):
        self.socket.send(data)
    
    def close(self):
        SimpleServiceHandler.close(self)
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket = None
            except:
                pass
            


class TCPServiceServer:
    def __init__(self, service, ConnectionHandler = SocketServiceHandler, messageDelimiter=""):
        self.service = service
        self.ConnectionHandler = ConnectionHandler
        self.messageDelimiter=messageDelimiter
        
    def serve(self, address):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(address)        
        self.socket.listen(5)
        print "serving", self.socket
        while 1:
            (conn,addr) = self.socket.accept()
            self.acceptConnection(conn)
    
    def acceptConnection(self, conn):
        self.handleConnection(conn)
    
    def handleConnection(self, conn):
        self.ConnectionHandler(conn, self.service, messageDelimiter=self.messageDelimiter).receiveForever()
    


class ThreadingMixin:
    def acceptConnection(self, conn):
        t = Thread(target=self.handleConnection, args=(conn,))
        t.setDaemon(True)
        t.start()

class ThreadedTCPServiceServer(ThreadingMixin, TCPServiceServer):
    pass
        
        
