def getChildIndex(parent, child):
    """
    var count = 0, current = parent.firstChild;
    while (current) {
        if (current.isSameNode(child))
            return count;
        if (current.nodeType == 1)
            ++count;
        current = current.nextSibling;
    }
    return -1;
    """

def isOrHasChild(parent, child):
    """
    while (child) {
      if (parent.isSameNode(child))
        return true;
      child = child.parentNode;
      if (child.nodeType != 1)
        child = null;
    }
    return false;
    """

def releaseCapture(elem):
    """
    if ((DOM_sCaptureElem != null) && DOM_compare(elem, DOM_sCaptureElem))
        DOM_sCaptureElem = null;
    
    if (elem.isSameNode($wnd.__captureElem))
        $wnd.__captureElem = null;
    """

def compare(elem1, elem2):
    """
    if (!elem1 && !elem2)
        return true;
    else if (!elem1 || !elem2)
        return false;
    return (elem1.isSameNode(elem2));
    """


