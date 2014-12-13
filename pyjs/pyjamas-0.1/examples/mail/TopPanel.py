import Window
from ui import ClickListener, Composite, HTML, HorizontalPanel, VerticalPanel, Widget, HasAlignment
from AboutDialog import AboutDialog
from Logger import Logger

class TopPanel(Composite):

    def __init__(self):
        self.signOutLink = HTML("<a href='javascript:;'>Sign Out</a>")
        self.aboutLink = HTML("<a href='javascript:;'>About</a>")

        outer = HorizontalPanel()
        inner = VerticalPanel()

        outer.setHorizontalAlignment(HasAlignment.ALIGN_RIGHT)
        inner.setHorizontalAlignment(HasAlignment.ALIGN_RIGHT)

        links = HorizontalPanel()
        links.setSpacing(4)
        links.add(self.signOutLink)
        links.add(self.aboutLink)

        outer.add(inner)
        inner.add(HTML("<b>Welcome back, foo@example.com</b>"))
        inner.add(links)

        self.signOutLink.addClickListener(self)
        self.aboutLink.addClickListener(self)

        self.setWidget(outer)
        inner.setStyleName("mail-TopPanel")
        links.setStyleName("mail-TopPanelLinks")

    def onClick(self, sender):
        if (sender == self.signOutLink):
            Window.alert("If this were implemented, you would be signed out now.")
        elif (sender == self.aboutLink):
            # When the 'About' item is selected, show the AboutDialog.
            # Note that showing a dialog box does not block -- execution continues
            # normally, and the dialog fires an event when it is closed.
            dlg = AboutDialog()

            # Position it roughly in the middle of the screen.
            left = (Window.getClientWidth() - 512) / 2
            top = (Window.getClientHeight() - 256) / 2
            Logger("TopPanel", "left: " + left)
            Logger("TopPanel", "top: " + top)
            dlg.setPopupPosition(left, top)

            dlg.show()
