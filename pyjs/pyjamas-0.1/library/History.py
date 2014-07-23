historyListeners = []
init()

def init():
    """
    $wnd.__historyToken = '';

    // Get the initial token from the url's hash component.
    var hash = $wnd.location.hash;
    if (hash.length > 0)
        $wnd.__historyToken = hash.substring(1);

    // Create the timer that checks the browser's url hash every 1/4 s.
    $wnd.__checkHistory = function() {
        var ctx = '', locn = $wnd.location.href;
        var hashIdx = locn.indexOf('#');
        if (hashIdx != -1)
            ctx = locn.substring(hashIdx + 1);

        if (ctx != $wnd.__historyToken) {
            // TODO - move init back into History
            // this.onHistoryChanged(ctx);
            var h = new __History_History();
            h.onHistoryChanged(ctx);
            $wnd.__historyToken = ctx;
        }

        $wnd.setTimeout('__checkHistory()', 250);
    };

    // Kick off the timer.
    $wnd.__checkHistory();

    return true;
    """

class History:

    def addHistoryListener(self, listener):
        global historyListeners
        historyListeners.append(listener)

    def back(self):
        """
        $wnd.history.back();
        """

    def forward(self):
        """
        $wnd.history.forward();
        """
    
    def getToken(self):
        """
        return $wnd.__historyToken;
        """
    
    def newItem(self, historyToken):
        """
        var locn = $wnd.location.href;
        var hashIdx = locn.indexOf('#');
        if (hashIdx != -1)
            locn = locn.substring(0, hashIdx);
        $wnd.location.href = locn + '#' + historyToken;
        """

    # TODO - fireHistoryChangedAndCatch not implemented
    def onHistoryChanged(self, historyToken):
        #UncaughtExceptionHandler handler = GWT.getUncaughtExceptionHandler();
        #if (handler != null)
        #   fireHistoryChangedAndCatch(historyToken, handler);
        #else
        self.fireHistoryChangedImpl(historyToken)

    # TODO
    def fireHistoryChangedAndCatch(self):
        pass
    
    def fireHistoryChangedImpl(self, historyToken):
        global historyListeners
        
        for listener in historyListeners:
            listener.onHistoryChanged(historyToken)

    def removeHistoryListener(self, listener):
        global historyListeners
        historyListeners.remove(listener)

