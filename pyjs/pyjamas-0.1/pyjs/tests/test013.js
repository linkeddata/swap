function ui_FocusWidget(element) {
    return new __ui_FocusWidget(element);
}
function __ui_FocusWidget(element) {
    this.clickListeners = new pyjslib_List([]);
}
__ui_FocusWidget.prototype.addClickListener = function(listener) {
    this.clickListeners.append(listener);
};
__ui_FocusWidget.prototype.onBrowserEvent = function(event) {
    if ((DOM_eventGetType(event) == __ui_Event.ONCLICK)) {

        var __listener = this.clickListeners.__iter__();
        try {
            while (true) {
                var listener = __listener.next();
                
        
    listener(this);

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }
        
    }
};
