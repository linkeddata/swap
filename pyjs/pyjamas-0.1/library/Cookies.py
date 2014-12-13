def getCookie(key):
    """
    var cookies = Cookies_loadCookies();
    var value = cookies[key];
    if (value)
        return value;
    else
        return null;
    """

def loadCookies():
    """
    var cookies = {};
    
    var docCookie = $doc.cookie;
    if (docCookie && docCookie != '') {
        var crumbs = docCookie.split('; ');
        for (var i = 0; i < crumbs.length; ++i) {
            var parts = crumbs[i].split("=");
            if (parts.length == 2) {
                cookies[parts[0]] = unescape(parts[1]);
            }
        }
    }
    
    return cookies;
    """


