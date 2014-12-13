import pygwt

class HTTPRequest:
    def asyncPost(self, url, postData, handler):
        moduleName=pygwt.getModuleName()
        return self.asyncPostImpl(None, None, url, postData, handler, moduleName)

    def asyncGet(self, url, handler):
        moduleName=pygwt.getModuleName()
        return self.asyncGetImpl(None, None, url, handler, moduleName)

    def doCreateXmlHTTPRequest(self):
        """
        return new XMLHttpRequest();
        """

    def asyncPostImpl(self, user, pwd, url, postData, handler, moduleName):
        """
        var xmlHttp = this.doCreateXmlHTTPRequest();
        try {
            xmlHttp.open("POST", url, true);
            xmlHttp.setRequestHeader("Content-Type", "text/plain; charset=utf-8");
            if (moduleName) {
                xmlHttp.setRequestHeader("X-PYGWTCallingModule", moduleName);
            }
            xmlHttp.onreadystatechange = function() {
                if (xmlHttp.readyState == 4) {
                    handler.onCompletion(xmlHttp.responseText);
                    xmlHttp = null;
                }
            };
            xmlHttp.send(postData);
            return true;
        }
        catch (e) {
            return false;
        }
        """

    def asyncGetImpl(self, user, pwd, url, handler, moduleName):
        """
        var xmlHttp = this.doCreateXmlHTTPRequest();
        try {
            xmlHttp.open("GET", url, true);
            xmlHttp.setRequestHeader("Content-Type", "text/plain; charset=utf-8");
            if (moduleName) {
                xmlHttp.setRequestHeader("X-PYGWTCallingModule", moduleName);
            }
            xmlHttp.onreadystatechange = function() {
                if (xmlHttp.readyState == 4) {
                    handler.onCompletion(xmlHttp.responseText);
                    xmlHttp = null;
                }
            };
            xmlHttp.send('');
            return true;
        }
        catch (e) {
            return false;
        }
        """
