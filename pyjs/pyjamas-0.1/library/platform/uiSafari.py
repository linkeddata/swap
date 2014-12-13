class Focus:
    def blur(self, elem):
        """
        elem.__anchor.blur();
        """
    
    def createFocusable(self):
        """
        var div = document.createElement('div');
        var input = document.createElement('input');
        input.type = 'text';
        input.style.zIndex = -1;
        input.style.position = 'absolute';
        
        div.addEventListener(
            'click',
            function() { input.focus(); },
            false);
        
        div.appendChild(input);
        div.__anchor = input;
        return div;
        """

    def focus(self, elem):
        """
        elem.__anchor.focus();
        """
    
    def getTabIndex(self, elem):
        """
        return elem.__anchor.tabIndex;
        """
    
    def setAccessKey(self, elem, key):
        """
        elem.__anchor.accessKey = key;
        """
    
    def setTabIndex(self, elem, index):
        """
        elem.__anchor.tabIndex = index;
        """
