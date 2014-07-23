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
        // is changing.
        if (token != $wnd.__historyToken) {
            $wnd.__historyToken = token;

            // TODO(jgw): fix the bookmark update, if possible.  The following code
            // screws up the browser by (a) making it pretend that it's loading the
            // page indefinitely, and (b) causing all text to disappear (!)
            //        var base = $wnd.location.href;
            //        var hashIdx = base.indexOf('#');
            //        if (hashIdx != -1)
            //          base = base.substring(0, hashIdx);
            //        $wnd.location.replace(base + '#' + token);

            // TODO - move init back into History
            // this.onHistoryChanged(token);
            var h = new __History_History();
            h.onHistoryChanged(token);
        }
    };

    return true;
    """

        
class History:

    def newItem(self, historyToken):
        """
        var iframe = $doc.getElementById('__pygwt_historyFrame');
        iframe.contentWindow.location.href = 'history.html?' + historyToken;
        """
