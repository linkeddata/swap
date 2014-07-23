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

class JSONRPCError:
    pass

class DecodingJSONFailed(JSONRPCError):
    pass

class InvalidJSONMessage(JSONRPCError):
    pass

class MethodNotFound(JSONRPCError):
    pass

class InvalidMethodParameters(JSONRPCError):
    pass
class MethodNameNotAllowed(JSONRPCError):
    pass
    
    

def getTracebackStr():
    import traceback
    import StringIO
    s=StringIO.StringIO("")
    traceback.print_exc(file=s)
    return s.getvalue()