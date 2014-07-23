def init():
    """
    // Check for existence of the history frame.
    var historyFrame = $doc.getElementById('__pygwt_historyFrame');
    if (!historyFrame)
        return false;

    // Get the initial token from the url's hash component.
    var hash = $wnd.location.hash;
    if (hash.length > 0)
        $wnd.__historyToken = hash.substring(1);
    else
        $wnd.__historyToken = '';

    // Initialize the history iframe.  If '__historyToken' already exists, then
    // we're probably backing into the app, so _don't_ set the iframe's location.
    var tokenElement = null;
    if (historyFrame.contentWindow) {
        var doc = historyFrame.contentWindow.document;
        tokenElement = doc ? doc.getElementById('__historyToken') : null;
    }

    if (tokenElement)
        $wnd.__historyToken = tokenElement.value;
    else
        historyFrame.src = 'history.html?' + $wnd.__historyToken;

    // Expose the '__onHistoryChanged' function, which will be called by
    // the history frame when it loads.
    $wnd.__onHistoryChanged = function(token) {
        // Change the URL and notify the application that its history frame
        // is changing.  Note that setting location.hash does _not_ add a history
        // frame on IE, so we don't have to do a 'location.replace()'.
        if (token != $wnd.__historyToken) {
            $wnd.__historyToken = token;
            $wnd.location.hash = token;
            // TODO - move init back into History
            // this.onHistoryChanged(token);
            var h = new __History_History();
            h.onHistoryChanged(token);
        }
    };

    // This is the URL check timer.  It detects when an unexpected change
    // occurs in the document's URL (e.g. when the user enters one manually
    // or selects a 'favorite', but only the #hash part changes).  When this
    // occurs, we _must_ reload the page.  This is because IE has a really
    // nasty bug that totally mangles its history stack and causes the location
    // bar in the UI to stop working under these circumstances.
    var urlChecker = function() {
        var hash = $wnd.location.hash;
        if (hash.length > 0) {
            var token = hash.substring(1);
            if ($wnd.__historyToken && (token != $wnd.__historyToken))
                $wnd.location.reload();
        }
        $wnd.setTimeout(urlChecker, 250);
    };
    urlChecker();

    return true;
    """


class History:

    def newItem(self, historyToken):
        """
        var iframe = $doc.getElementById('__pygwt_historyFrame');
        iframe.contentWindow.location.href = 'history.html?' + historyToken;
        """
