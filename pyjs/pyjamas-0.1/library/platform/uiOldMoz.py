class Focus:
    def blur(self, elem):
        pass
    
    def createFocusable(self):
        """
        var e = $doc.createElement("DIV");
        e.style.MozUserFocus = 'normal';
        return e;
        """

    def focus(self, elem):
        pass
    
    def getTabIndex(self, elem):
        return -1
    
    def setTabIndex(self, elem, index):
        pass
