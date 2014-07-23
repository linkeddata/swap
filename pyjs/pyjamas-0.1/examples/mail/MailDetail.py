from ui import Composite, DockPanel, HTML, ScrollPanel, VerticalPanel
from Logger import Logger

class MailDetail(Composite):
    def __init__(self):
        panel = VerticalPanel()
        headerPanel = VerticalPanel()
        self.subject = HTML()
        self.sender = HTML()
        self.recipient = HTML()
        self.body = HTML()
        self.scroller = ScrollPanel(self.body)

        self.body.setWordWrap(True)

        headerPanel.add(self.subject)
        headerPanel.add(self.sender)
        headerPanel.add(self.recipient)
        headerPanel.setWidth("100%")

        innerPanel = DockPanel()
        innerPanel.add(headerPanel, DockPanel.NORTH)
        innerPanel.add(self.scroller, DockPanel.CENTER)

        innerPanel.setCellHeight(self.scroller, "100%")
        panel.add(innerPanel)
        innerPanel.setSize("100%", "100%")
        self.scroller.setSize("100%", "100%")
        self.setWidget(panel)

        self.setStyleName("mail-Detail")
        headerPanel.setStyleName("mail-DetailHeader")
        innerPanel.setStyleName("mail-DetailInner")
        self.subject.setStyleName("mail-DetailSubject")
        self.sender.setStyleName("mail-DetailSender")
        self.recipient.setStyleName("mail-DetailRecipient")
        self.body.setStyleName("mail-DetailBody")
        Logger("Mail detail", " ")

    def setItem(self, item):
        self.subject.setHTML(item.subject)
        self.sender.setHTML("<b>From:</b>&nbsp;" + item.sender)
        self.recipient.setHTML("<b>To:</b>&nbsp;foo@example.com")
        self.body.setHTML(item.body)
        
    def adjustSize(self, windowWidth, windowHeight):
        scrollWidth = windowWidth - self.scroller.getAbsoluteLeft() - 9
        if (scrollWidth < 1):
            scrollWidth = 1

        scrollHeight = windowHeight - self.scroller.getAbsoluteTop() - 9
        if (scrollHeight < 1):
            scrollHeight = 1

        self.scroller.setSize("" + scrollWidth, "" + scrollHeight)

