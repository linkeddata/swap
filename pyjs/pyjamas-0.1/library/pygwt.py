sNextHashId = 0

def getNextHashId():
    global sNextHashId
    sNextHashId += 1
    return sNextHashId

def getHashCode(o):
    """
    return (o!=null?(o.$H?o.$H:o.$H=pygwt_getNextHashId()):0);
    """

def getModuleName():
    """
    return $moduleName;
    """

def getModuleBaseURL():
    """
    // this is intentionally not using $doc, because we want the module's own url
    var s = document.location.href;
    
    // Pull off any hash.
    var i = s.indexOf('#');
    if (i != -1)
        s = s.substring(0, i);
    
    // Pull off any query string.
    i = s.indexOf('?');
    if (i != -1)
        s = s.substring(0, i);
    
    // Rip off everything after the last slash.
    i = s.lastIndexOf('/');
    if (i != -1)
        s = s.substring(0, i);
    return s;
    """
