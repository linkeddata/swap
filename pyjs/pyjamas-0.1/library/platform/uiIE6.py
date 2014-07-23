class PopupPanel:
    # PopupImpl.createElement
    def createElement(self):
        """
        var outer = $doc.createElement('div');
        var frame = $doc.createElement('iframe');
        
        outer.appendChild(frame);
        frame.scrolling = 'no';
        frame.style.zIndex = -1;
        frame.frameBorder = 0;
        
        outer.style.position = 'absolute';
        frame.style.position = 'absolute';
        return outer;
        """
    
    # PopupImpl.fixup
    def fixup(self, popup):
        """
        popup.children[0].style.width = popup.children[1].offsetWidth;
        popup.children[0].style.height = popup.children[1].offsetHeight;
        """

    # PopupImpl.setChild
    def setChild(self, popup, child):
        """
        if (popup.children.length == 2)
            popup.removeChild(popup.children[1]);
        popup.appendChild(child);
        """

    # PopupImpl.setClassName
    def setClassName(self, popup, className):
        """
        popup.children[1].className = className;
        """

    # PopupImpl.setHeight
    def setHeight(self, height):
        """
        popup.style.height = popup.children[0].style.height = popup.children[1].style.height = height;
        """

    # PopupImpl.setWidth
    def setWidth(self, width):
        """
        popup.style.width = popup.children[0].style.width = popup.children[1].style.width = width;
        """


class TextBoxBase:
    def getCursorPos(self):
        """
        try {
            var elem = this.getElement();
            var tr = elem.document.selection.createRange();
            if (tr.parentElement().uniqueID != elem.uniqueID)
                return -1;
            return -tr.move("character", -65535);
        }
        catch (e) {
            return 0;
        }
        """

    def getSelectionLength(self):
        """
        try {
            var elem = this.getElement();
            var tr = elem.document.selection.createRange();
            if (tr.parentElement().uniqueID != elem.uniqueID)
                return 0;
            return tr.text.length;
        }
        catch (e) {
            return 0;
        }
        """

    def setSelectionRange(self, pos, length):
        """
        try {
            var elem = this.getElement();
            var tr = elem.createTextRange();
            tr.collapse(true);
            tr.moveStart('character', pos);
            tr.moveEnd('character', length);
            tr.select();
        }
        catch (e) {
        }
        """

class TextArea:
    def getCursorPos(self):
        """
        try {
            var elem = this.getElement();
            var tr = elem.document.selection.createRange();
            var tr2 = tr.duplicate();
            tr2.moveToElementText(elem);
            tr.setEndPoint('StartToStart', tr2);
            return tr.text.length;
        }
        catch (e) {
            return 0;
        }
        """


