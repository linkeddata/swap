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
from mod_python import apache
from jsonrpc import SimpleServiceHandler


class ModPyHandler(SimpleServiceHandler):
    def send(self, data):
        self.req.write(data)
        self.req.flush()
        
    def handle(self, req):
        self.req = req
        req.content_type = "text/plain"
        self.handlePartialData(req.read())
        self.close()

from mod_python import apache
import os, sys

def handler(req):    
    (modulePath, fileName) = os.path.split(req.filename)
    (moduleName, ext) = os.path.splitext(fileName)
    
    if not os.path.exists(os.path.join(modulePath, moduleName + ".py")):
        return apache.HTTP_NOT_FOUND
        
    if not modulePath in sys.path:
        sys.path.insert(0, modulePath)
    
    module = apache.import_module(moduleName, log=1)
       
    if hasattr(module, "getService"):
        service = module.getService()
    elif hasattr(module, "service"):
        service = module.service
    elif hasattr(module, "Service"):
        service = module.Service()
    else:
        return apache.HTTP_SERVICE_UNAVAILABLE
    
    ModPyHandler(service, messageDelimiter="\n").handle(req)
    
    return apache.OK
    
