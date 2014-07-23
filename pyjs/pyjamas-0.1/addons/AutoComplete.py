# Autocomplete component for Pyjamas
# Ported by Willie Gollino from Autocomplete component for GWT - Originally by Oliver Albers http://gwt.components.googlepages.com/

from ui import TextBox, PopupPanel, ListBox, KeyboardListener, RootPanel

class AutoCompleteTextBox(TextBox):
    def __init__(self):
        self.choicesPopup = PopupPanel(True)
        self.choices = ListBox()
        self.items = SimpleAutoCompletionItems()
        self.popupAdded = False
        self.visible = False

        TextBox.__init__(self)
        self.addKeyboardListener(self)
        self.choices.addChangeListener(self)
        self.setStyleName("AutoCompleteTextBox")

        self.choicesPopup.add(self.choices)
        self.choicesPopup.addStyleName("AutoCompleteChoices")
            
        self.choices.setStyleName("list")

    def setCompletionItems(self, items):
        if not items.getCompletionItems:
            items = SimpleAutoCompletionItems(items)
        
        self.items = items

    def getCompletionItems(self):
        return self.items

    def onKeyDown(self, arg0, arg1, arg2):
        pass

    def onKeyPress(self, arg0, arg1, arg2):
        pass

    def onKeyUp(self, arg0, arg1, arg2):
        if arg1 == KeyboardListener.KEY_DOWN:
            selectedIndex = self.choices.getSelectedIndex()
            selectedIndex += 1
            if selectedIndex > self.choices.getItemCount():
                selectedIndex = 0
        
            self.choices.setSelectedIndex(selectedIndex)           
            return

        if arg1 == KeyboardListener.KEY_UP:
            selectedIndex = self.choices.getSelectedIndex()
            selectedIndex -= 1
            if selectedIndex < 0:
                selectedIndex = self.choices.getItemCount()
            self.choices.setSelectedIndex(selectedIndex)
            return

        if arg1 == KeyboardListener.KEY_ENTER:
            if self.visible:
                self.complete()      
            return

        if arg1 == KeyboardListener.KEY_ESCAPE:
            self.choices.clear()
            self.choicesPopup.hide()
            self.visible = False
            return

        text = self.getText()
        matches = []
        if len(text) > 0:
            matches = self.items.getCompletionItems(text)

        if len(matches) > 0:
            self.choices.clear()

            for i in range(len(matches)):
                self.choices.addItem(matches[i])
                
            if len(matches) == 1 and matches[0] == text:
                self.choicesPopup.hide()
            else:
                self.choices.setSelectedIndex(0)
                self.choices.setVisibleItemCount(len(matches) + 1)
                    
                if not self.popupAdded:
                    RootPanel().add(self.choicesPopup)
                    self.popupAdded = True

                self.choicesPopup.show()
                self.visible = True
                self.choicesPopup.setPopupPosition(self.getAbsoluteLeft(), self.getAbsoluteTop() + self.getOffsetHeight())
                self.choices.setWidth(self.getOffsetWidth() + "px")
        else:
            self.visible = False
            self.choicesPopup.hide()

    def onChange(self, arg0):
        self.complete()

    def onClick(self, arg0):
        self.complete()

    def complete(self):
        if self.choices.getItemCount() > 0:
            self.setText(self.choices.getItemText(self.choices.getSelectedIndex()))
            
        self.choices.clear()
        self.choicesPopup.hide()
        self.setFocus(True)


class SimpleAutoCompletionItems:
    def __init__(self, items = None):
        if items == None:
            items = []
        self.completions = items

    def getCompletionItems(self, match):
        matches = []        
        match = match.lower()
        
        for i in range(len(self.completions)):
            lower = self.completions[i].lower()
            if lower.startswith(match):
                matches.append(self.completions[i])
        
        return matches
