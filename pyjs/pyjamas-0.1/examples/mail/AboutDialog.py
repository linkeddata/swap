from ui import Button, ClickListener, DialogBox, DockPanel, HorizontalPanel, HTML, Image, KeyboardListener, Widget, HasAlignment

class AboutDialog(DialogBox):
    
  LOGO_IMAGE = "http://trac.pyworks.org/pyjamas/chrome/site/pyjamas-logo-small.png"

  def __init__(self):
      DialogBox.__init__(self)
      # Use this opportunity to set the dialog's caption.
      self.setText("About the Mail Sample")

      # Create a DockPanel to contain the 'about' label and the 'OK' button.
      outer = DockPanel()
      outer.setSpacing(4)
      
      outer.add(Image(AboutDialog.LOGO_IMAGE), DockPanel.WEST)

      # Create the 'OK' button, along with a listener that hides the dialog
      # when the button is clicked. Adding it to the 'south' position within
      # the dock causes it to be placed at the bottom.
      buttonPanel = HorizontalPanel()
      buttonPanel.setHorizontalAlignment(HasAlignment.ALIGN_RIGHT)
      buttonPanel.add(Button("Close", self))
      outer.add(buttonPanel, DockPanel.SOUTH)

      # Create the 'about' label. Placing it in the 'rest' position within the
      # dock causes it to take up any remaining space after the 'OK' button
      # has been laid out.

      textplain =  "This sample application demonstrates the construction "
      textplain += "of a complex user interface using pyjamas' built-in widgets.  Have a look "
      textplain += "at the code to see how easy it is to build your own apps!"
      text = HTML(textplain)
      text.setStyleName("mail-AboutText")
      outer.add(text, DockPanel.CENTER)

      # Add a bit of spacing and margin to the dock to keep the components from
      # being placed too closely together.
      outer.setSpacing(8)

      self.add(outer)

  def onClick(self, sender):
      self.hide()
      
  def onKeyDownPreview(self, key, modifiers):
      # Use the popup's key preview hooks to close the dialog when either
      # enter or escape is pressed.
      if (key == KeyboardListener.KEY_ESCAPE or key == KeyboardListener.KEY_ENTER):
          self.hide()
      return True
