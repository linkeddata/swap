from ui import ClickListener, Composite, HTML, HorizontalPanel, Image, PopupPanel, VerticalPanel, Widget, Label
from Logger import Logger

class Contact:
    def __init__(self, name, email):
        self.photo = "http://code.google.com/webtoolkit/documentation/examples/desktopclone/default_photo.jpg"
        self.name = name
        self.email = email

class ContactPopup(PopupPanel):
    def __init__(self, contact):
        # The popup's constructor's argument is a boolean specifying that it
        # auto-close itself when the user clicks outside of it.

        PopupPanel.__init__(self, True)

        inner = VerticalPanel()
        nameLabel = Label(contact.name)
        emailLabel = Label(contact.email)
        inner.add(nameLabel)
        inner.add(emailLabel)
        
        panel = HorizontalPanel()
        panel.setSpacing(4)
        panel.add(Image(contact.photo))
        panel.add(inner)
        
        self.add(panel)
        self.setStyleName("mail-ContactPopup")
        nameLabel.setStyleName("mail-ContactPopupName")
        emailLabel.setStyleName("mail-ContactPopupEmail")


class Contacts(Composite):
    def __init__(self):
        self.contacts = []
        self.contacts.append(Contact("Benoit Mandelbrot", "benoit@example.com"))
        self.contacts.append(Contact("Albert Einstein", "albert@example.com"))
        self.contacts.append(Contact("Rene Descartes", "rene@example.com"))
        self.contacts.append(Contact("Bob Saget", "bob@example.com"))
        self.contacts.append(Contact("Ludwig von Beethoven", "ludwig@example.com"))
        self.contacts.append(Contact("Richard Feynman", "richard@example.com"))
        self.contacts.append(Contact("Alan Turing", "alan@example.com"))
        self.contacts.append(Contact("John von Neumann", "john@example.com"))

        self.panel = VerticalPanel()

        # Add all the contacts to the list.
        i = 0
        while (i < len(self.contacts)):
            self.addContact(self.contacts[i])
            i =  i + 1

        self.setWidget(self.panel)
        self.setStyleName("mail-Contacts")

    def addContact(self, contact):
        link = HTML("<a href='javascript:;'>" + contact.name + "</a>")
        self.panel.add(link)
        
        # Add a click listener that displays a ContactPopup when it is clicked.
        listener = ContactListener(contact, link)
        link.addClickListener(listener)

class ContactListener:
    def __init__(self, contact, link):
        self.cont = contact
        self.link = link
        
    def onClick(self, sender):
        if (sender == self.link):
            popup = ContactPopup(self.cont)
            left = self.link.getAbsoluteLeft() + 32
            top = self.link.getAbsoluteTop() + 8
            popup.setPopupPosition(left, top)
            popup.show()
