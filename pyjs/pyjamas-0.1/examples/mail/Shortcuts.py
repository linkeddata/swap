from ui import Composite, StackPanel, Label
from Tasks import Tasks
from Mailboxes import Mailboxes
from Contacts import Contacts

class Shortcuts(Composite):

    def __init__(self):
        stackPanel = StackPanel()
        stackPanel.add(Mailboxes(), self.createHeaderHTML("mailgroup.gif", "Mail"), True)
        stackPanel.add(Tasks(), self.createHeaderHTML("tasksgroup.gif", "Tasks"), True)
        stackPanel.add(Contacts(), self.createHeaderHTML("contactsgroup.gif", "Contacts"), True)

        stackPanel.showStack(0)

        self.setWidget(stackPanel)

    def createHeaderHTML(self, imageUrl, caption):
        header =  "<table align='left'><tr>" + "<td><img src='"
        header += "http://code.google.com/webtoolkit/documentation/examples/desktopclone/"
        header += imageUrl + "'></td>"
        header += "<td style='vertical-align:middle'><b style='white-space:nowrap'>"
        header +=  caption + "</b></td>" + "</tr></table>"
        return header
