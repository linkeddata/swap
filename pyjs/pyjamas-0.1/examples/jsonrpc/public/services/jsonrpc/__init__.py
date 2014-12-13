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

from threading import  Event,  Lock

from errors import *

from simplejson import JSONDecoder, JSONEncoder
    
    
class JSONRPCEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, JSONRPCError):
            return obj.__class__.__name__
        else:
            return JSONEncoder.default(self, obj)


class Timeout(Exception):
    pass
    
class ResponseEvent:
    """Event which is fired when the response is returned for a request.
    
        For each request sent this event is created. 
        An application can wait for the event to create a blocking request.
    """
    def __init__(self):
        self.__evt = Event()
        
    def waiting(self):
        return not self.__evt.isSet()
        
    def waitForResponse(self, timeOut=None):
        """blocks until the response arrived or timeout is reached."""
        self.__evt.wait(timeOut)
        if self.waiting():
            raise Timeout()
        else:
            if self.response["error"]:
                raise Exception(self.response["error"])
            else:
                return self.response["result"]
        
    def handleResponse(self, resp):
        self.response = resp
        self.__evt.set()
        
        
class SimpleMessageHandler:
    def __init__(self,  DecoderClass=JSONDecoder, EncoderClass=JSONRPCEncoder, messageDelimiter=""):
        self.decoder = DecoderClass()
        self.encoder = EncoderClass()
        self.partialData = ""
        self.respEvents={}
        self.respLock = Lock()
        self.messageDelimiter=messageDelimiter
        
    def close(self):
        pass
        
    def send(self, data):
        pass
        
    def sendMessage(self, msg):
        self.send(self.encoder.encode(msg) + self.messageDelimiter)
    
    def handlePartialData(self, data):
        data = self.partialData + data.replace("\r","").replace("\n", "")
        msgs=[]
        while data != "":
            pos = data.find("{")
            if(pos > -1):
                data=data[pos:]
                try:
                    (obj, pos) = self.decoder.raw_decode(data)
                    data = data[pos:]
                    msgs.append(obj)    
                except:
                    break
            else:
                break
        self.partialData = data
        
        self.handleMessages(msgs)

    def sendNotify(self, name, args):
        """sends a notification object to the peer"""
        self.sendMessage({"method":name, "params": args})
        
    def sendRequest(self, name, args):
        """sends a request to the peer"""
        (respEvt, id) = self.newResponseEvent()
        self.sendMessage({"id":id, "method":name, "params": args})
        return respEvt
        
    def sendResponse(self, id, result, error):
        """sends a response to the peer"""
        self.sendMessage({"result":result, "error": error, "id":id})
    
    def newResponseEvent(self):
        """creates a response event and adds it to a waiting list
           When the reponse arrives it will be removed from the list. 
        """
        respEvt = ResponseEvent()
        self.respLock.acquire()
        eid = id(respEvt)
        self.respEvents[eid] = respEvt
        self.respLock.release()
        return (respEvt,eid)
        
    def handleMessages(self, msgs):
        for msg in msgs:
            if msg.has_key("method") and msg.has_key("params"):
                if msg.has_key("id"):
                    if msg["id"]:
                        self.handleRequest(msg)    
                    else:
                        self.handleNotification(msg)
                else:
                    self.handleNotification(msg)
            elif msg.has_key("result") and msg.has_key("error"):
                self.handleResponse(msg)
            else:#unknown object 
                self.sendResponse(None, InvalidJSONMessage())
                self.close()
                
    def handleResponse(self, resp):
        """handles a response by fireing the response event for the response coming in"""
        id=resp["id"]
        evt = self.respEvents[id]
        del(self.respEvents[id])
        evt.handleResponse(resp)
    
    def handleRequest(self, request):
        pass
    def handleNotification(self, notification):
        pass
        
        
import re
NameAllowedRegExp=re.compile("^[a-zA-Z]\w*$")
def nameAllowed(name):
    """checks if a name is allowed.
    """
    if NameAllowedRegExp.match(name):
        return 1
    else:
        return 0
    
def getMethodByName(obj, name):

    """searches for an object with the name given inside the object given.
       "obj.child.meth" will return the meth obj.
    """
    try:#to get a method by asking the service
        obj = obj._getMethodByName(name)
    except:
        #assumed a childObject is ment 
        #split the name from objName.childObjName... -> [objName, childObjName, ...]
        #and get all objects up to the last in list with name checking from the service object
        names = name.split(".")
        for name in names:
            if nameAllowed(name):
                obj = getattr(obj, name)
            else:
                raise MethodNameNotAllowed()
        
    return obj  
    


class SimpleServiceHandler(SimpleMessageHandler):
    def __init__(self, service, DecoderClass=JSONDecoder, EncoderClass=JSONRPCEncoder, messageDelimiter=""):
        self.service = service
        SimpleMessageHandler.__init__(self, DecoderClass, EncoderClass, messageDelimiter)
        try:
            service._newConnection(self)
        except:
            pass
        
    def close(self):
        try:
            self.service._closingConnection(self)
        except:
            pass
        
    def handleRequest(self, req):
        """handles a request by calling the appropriete method the service exposes"""
        name = req["method"]
        params = req["params"]
        id=req["id"]
        obj=None
        try: #to get a callable obj 
            obj = getMethodByName(self.service, name)
        except MethodNameNotAllowed,e:
            self.sendResponse(id, None, e)
        except:
            self.sendResponse(id, None, MethodNotFound())
        if obj:
            try: #to call the object with parameters
                rslt = obj(*params)
                self.sendResponse(id, rslt, None)
            except TypeError: # wrong arguments
                #todo what if the TypeError was not thrown directly by the callable obj
                s=getTracebackStr()
                self.sendResponse(id, None, InvalidMethodParameters())
            except: #error inside the callable object
                s=getTracebackStr()
                self.sendResponse(id, None, s)
                
    def handleNotification(self, req):
        """handles a notification request by calling the appropriete method the service exposes"""
        name = req["method"]
        params = req["params"]
        try: #to get a callable obj 
            obj = getMethodByName(self.service, name)
            rslt = obj(*params)
        except:
            pass
                
    
    

