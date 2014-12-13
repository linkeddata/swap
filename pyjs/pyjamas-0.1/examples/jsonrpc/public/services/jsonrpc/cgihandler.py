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
import sys,os


class CGIHandler(SimpleServiceHandler):
    def __init__(self, service, messageDelimiter="\n"):
        self.sendData =[]
        SimpleServiceHandler.__init__(self, service, messageDelimiter=messageDelimiter)

    
    def send(self, data):
        self.sendData.append(data)
        
    def handle(self):
        try:
            contLen=int(os.environ['CONTENT_LENGTH'])
            data = sys.stdin.read(contLen)
        except:
            data = ""
        #execute the request
        self.handlePartialData(data) 
        self.sendReply()
        self.close()
    
    def sendReply(self):
        data = "\n".join(self.sendData)
        response = "Content-Type: text/plain\n"
        response += "Content-Length: %d\n\n" % len(data)
        response += data
        
        #on windows all \n are converted to \r\n if stdout is a terminal and  is not set to binary mode :(
        #this will then cause an incorrect Content-length.
        #I have only experienced this problem with apache on Win so far.
        if sys.platform == "win32":
            import  msvcrt
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
        #put out the response
        sys.stdout.write(response)
        
        
def handleCGIRequest(service):
    CGIHandler(service,messageDelimiter="\n").handle()
