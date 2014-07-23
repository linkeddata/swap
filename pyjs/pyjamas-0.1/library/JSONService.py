from HTTPRequest import HTTPRequest
import pygwt
from JSONParser import JSONParser

# no stream support
class JSONService:
    def __init__(self, url, handler = None):
        self.parser = JSONParser()
        self.url = url
        self.handler = handler
    
    def callMethod(self, method, params, handler = None):
        if handler == None:
            handler = self.handler
            
        if handler == None:
            return self.__sendNotify(method, params)
        else:
            return self.__sendRequest(method, params, handler)
    
    def onCompletion(self):
        pass

    def __sendNotify(self, method, params):
        msg = {"id":None, "method":method, "params":params}
        msg_data = self.parser.encode(msg)
        if not HTTPRequest().asyncPost(self.url, msg_data, self):
            return -1
        return 1

    def __sendRequest(self, method, params, handler):
        id = pygwt.getNextHashId()
        msg = {"id":id, "method":method, "params":params}
        msg_data = self.parser.encode(msg)
        
        request_info = JSONRequestInfo(id, method, handler)
        if not HTTPRequest().asyncPost(self.url, msg_data, JSONResponseTextHandler(request_info)):
            return -1
        return id


class JSONRequestInfo:
    def __init__(self, id, method, handler):
        self.id = id
        self.method = method
        self.handler = handler
    

class JSONResponseTextHandler:
    def __init__(self, request):
        self.request = request

    def onCompletion(self, json_str):
        response=JSONParser().decodeAsObject(json_str)
        
        if not response:
            self.request.handler.onRemoteError(0, "Server Error or Invalid Response", self.request)
        elif response["error"]:
            error = response["error"]
            self.request.handler.onRemoteError(error["code"], error["message"], self.request)
        else:
            self.request.handler.onRemoteResponse(response["result"], self.request)


# reserved names: callMethod, onCompletion
class JSONProxy(JSONService):
    def __init__(self, url, methods=None):
        JSONService.__init__(self, url)
        if methods:
            self.__registerMethods(methods)

    def __registerMethods(self, methods):
        """
        methods=methods.l;
        for (var i in methods) {
            var method = methods[i];
            this[method]=function() {
                var params = [];
                for (var n=0; n<arguments.length; n++) { params.push(arguments[n]); }
                if (params[params.length-1].onRemoteResponse) {
                    var handler=params.pop();
                    return this.__sendRequest(method, params, handler);
                    }
                else {
                    return this.__sendNotify(method, params);
                    }
                }
            }
        """


        
    
    

