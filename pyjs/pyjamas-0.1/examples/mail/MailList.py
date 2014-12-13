from ui import ClickListener, Composite, FlexTable, HTML, HorizontalPanel, SourcesTableEvents, TableListener, Widget, Label, HasAlignment
from MailItems import MailItems
from Logger import Logger

class MailList(Composite):

    VISIBLE_EMAIL_COUNT = 10

    def __init__(self, mailObject):
        self.countLabel = HTML()
        self.newerButton = HTML("<a href='javascript:;'>&lt; newer</a>", True)
        self.olderButton = HTML("<a href='javascript:;'>older &gt;</a>", True)
        self.startIndex = 0
        self.selectedRow = -1
        self.table = FlexTable()
        self.navBar = HorizontalPanel()
        self.mailObject = mailObject

        # Setup the table.
        self.table.setCellSpacing(0)
        self.table.setCellPadding(2)
        self.table.setWidth("100%")

        # Hook up events.
        self.table.addTableListener(self)
        self.newerButton.addClickListener(self)
        self.olderButton.addClickListener(self)

        # Create the 'navigation' bar at the upper-right.
        innerNavBar = HorizontalPanel()
        innerNavBar.setStyleName("mail-ListNavBar")
        innerNavBar.setSpacing(8)
        innerNavBar.add(self.newerButton)
        innerNavBar.add(self.countLabel)
        innerNavBar.add(self.olderButton)

        self.navBar.setHorizontalAlignment(HasAlignment.ALIGN_RIGHT)
        self.navBar.add(innerNavBar)
        self.navBar.setWidth("100%")

        self.setWidget(self.table)
        self.setStyleName("mail-List")

        self.initTable()
        self.update()

    def onCellClicked(self, sender, row, cell):
        # Select the row that was clicked (-1 to account for header row).
        if (row > 0):
            self.selectRow(row - 1)

    def onClick(self, sender):
        if (sender == self.olderButton):
            # Move forward a page.
            self.startIndex = self.startIndex + MailList.VISIBLE_EMAIL_COUNT
            if (self.startIndex >= MailItems().getMailItemCount()):
                self.startIndex = self.startIndex - MailList.VISIBLE_EMAIL_COUNT
            else:
                self.styleRow(self.selectedRow, False)
                self.selectedRow = -1
                self.update()
    
        elif (sender == self.newerButton):
            # Move back a page.
            self.startIndex = self.startIndex - MailList.VISIBLE_EMAIL_COUNT
            if (self.startIndex < 0):
                self.startIndex = 0
            else:
                self.styleRow(self.selectedRow, False)
                self.selectedRow = -1
                self.update()

    def initTable(self):
        # Create the header row.
        self.table.setText(0, 0, "sender")
        self.table.setText(0, 1, "email")
        self.table.setText(0, 2, "subject")
        self.table.setWidget(0, 3, self.navBar)
        self.table.getRowFormatter().setStyleName(0, "mail-ListHeader")

        # Initialize the rest of the rows.
        i = 0
        while i < MailList.VISIBLE_EMAIL_COUNT:
            self.table.setText(i + 1, 0, "")
            self.table.setText(i + 1, 1, "")
            self.table.setText(i + 1, 2, "")
            self.table.getCellFormatter().setWordWrap(i + 1, 0, False)
            self.table.getCellFormatter().setWordWrap(i + 1, 1, False)
            self.table.getCellFormatter().setWordWrap(i + 1, 2, False)
            self.table.getFlexCellFormatter().setColSpan(i + 1, 2, 2)
            i = i + 1


    def selectRow(self, row):
        # When a row (other than the first one, which is used as a header) is
        # selected, display its associated MailItem.
        item = MailItems().getMailItem(self.startIndex + row)
        if (item == None):
            return
                    
        self.styleRow(self.selectedRow, False)
        self.styleRow(row, True)

        item.read = True
        self.selectedRow = row
        self.mailObject.get().displayItem(item)


    def styleRow(self, row, selected):
        if (row != -1):
            if (selected):
                self.table.getRowFormatter().addStyleName(row + 1, "mail-SelectedRow")
            else:
                self.table.getRowFormatter().removeStyleName(row + 1, "mail-SelectedRow")

    def update(self):
        # Update the older/newer buttons & label.
        count = MailItems().getMailItemCount()
        max = self.startIndex + MailList.VISIBLE_EMAIL_COUNT
        if (max > count):
            max = count

        self.newerButton.setVisible(self.startIndex != 0)
        self.olderButton.setVisible(self.startIndex + MailList.VISIBLE_EMAIL_COUNT < count)
        startIndexPlusOne = self.startIndex + 1
        self.countLabel.setText("" + startIndexPlusOne + " - " + max + " of " + count)

        # Show the selected emails.
        i = 0
        while (i < MailList.VISIBLE_EMAIL_COUNT):
            # Don't read past the end.
            if (self.startIndex + i >= MailItems().getMailItemCount()):
                break

            item = MailItems().getMailItem(self.startIndex + i)

            # Add a row to the table, then set each of its columns to the
            # email's sender and subject values.

            self.table.setText(i + 1, 0, item.sender)
            self.table.setText(i + 1, 1, item.email)
            self.table.setText(i + 1, 2, item.subject)

            i = i + 1

        # Clear any remaining slots.
        while (i < MailList.VISIBLE_EMAIL_COUNT):
            self.table.setHTML(i + 1, 0, "&nbsp;")
            self.table.setHTML(i + 1, 1, "&nbsp;")
            self.table.setHTML(i + 1, 2, "&nbsp;")
            i = i + 1

        # Select the first row if none is selected.
        if (self.selectedRow == -1):
            self.selectRow(0)
