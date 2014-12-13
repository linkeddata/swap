def addWindowCloseListener(listener):
    # FIXME - need implementation
    self.closingListeners.append(listener)

def addWindowResizeListener(listener):
    # FIXME - need implementation
    self.resizeListeners.append(listener)

def alert(msg):
    """
    $wnd.alert(msg);
    """

def confirm(msg):
    """
    return $wnd.confirm(msg);
    """

def enableScrolling(enable):
    """
    $doc.body.style.overflow = enable ? 'auto' : 'hidden';
    """

def getClientHeight():
    """
    if ($wnd.innerHeight)
        return $wnd.innerHeight;
    return $doc.body.clientHeight;
    """

def getClientWidth():
    """
    if ($wnd.innerWidth)
        return $wnd.innerWidth;
    return $doc.body.clientWidth;
    """

def getTitle():
    """
    return $doc.title;
    """

def open(url, name, features):
    """
    $wnd.open(url, name, features);
    """

def removeWindowCloseListener(listener):
    closingListeners.remove(listener)

def removeWindowResizeListener(listener):
    resizeListeners.remove(listener)

def setMargin(size):
    """
    $doc.body.style.margin = size;
    """

def setTitle(title):
    """
    $doc.title = title;
    """

def onClosed():
    # FIXME - need implementation
    pass

def onClosing():
    # FIXME - need implementation
    pass

def onResize():
    # FIXME - need implementation
    pass

def fireClosedAndCatch(handler):
    # FIXME - need implementation
    pass

def fireClosedImpl():
    # FIXME - need implementation
    pass

def fireClosingAndCatch(handler):
    # FIXME - need implementation
    pass

def fireClosingImpl():
    # FIXME - need implementation
    pass

def fireResizedAndCatch(handler):
    # FIXME - need implementation
    pass

def fireResizedImpl():
    # FIXME - need implementation
    pass

def __init__(self):
    # FIXME - need implementation
    self.closingListeners = []
    self.resizeListeners = []
