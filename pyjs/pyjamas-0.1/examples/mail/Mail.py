# import com.google.gwt.core.client.EntryPoint;
# import com.google.gwt.user.client.Command;
# import com.google.gwt.user.client.DeferredCommand;
import Window
# import com.google.gwt.user.client.WindowResizeListener;
from ui import DockPanel, RootPanel, VerticalPanel
from MailDetail import MailDetail
from Shortcuts import Shortcuts
from MailList import MailList
from TopPanel import TopPanel
from Logger import Logger

class Mail:

    def get(self):
        return self.singleton

    def onModuleLoad(self):
        self.singleton = self

        topPanel = TopPanel()
        rightPanel = VerticalPanel()
        self.mailDetail = MailDetail()
        self.shortcuts = Shortcuts()

        topPanel.setWidth("100%")

        # MailList uses Mail.get() in its constructor, so initialize it after
        # 'singleton'.
        mailList = MailList(self.singleton)
        mailList.setWidth("100%")
        
        # Create the right panel, containing the email list & details.
        rightPanel.add(mailList)
        rightPanel.add(self.mailDetail)
        mailList.setWidth("100%")
        self.mailDetail.setWidth("100%")

        # Create a dock panel that will contain the menu bar at the top,
        # the shortcuts to the left, and the mail list & details taking the rest.
        outer = DockPanel()
        outer.add(topPanel, DockPanel.NORTH)
        outer.add(self.shortcuts, DockPanel.WEST)
        outer.add(rightPanel, DockPanel.CENTER)
        outer.setWidth("100%")

        outer.setSpacing(4)
        outer.setCellWidth(rightPanel, "100%")

        # Hook the window resize event, so that we can adjust the UI.
        #FIXME need implementation # Window.addWindowResizeListener(this)
        #Window.addWindowResizeListener(self)

        # Get rid of scrollbars, and clear out the window's built-in margin,
        # because we want to take advantage of the entire client area.
        Window.enableScrolling(False)
        Window.setMargin("0px")
        
        # Finally, add the outer panel to the RootPanel, so that it will be
        # displayed.
        #RootPanel.get().add(outer) # FIXME get#
        RootPanel().add(outer)
        RootPanel().add(Logger())
        
        # Call the window resized handler to get the initial sizes setup. Doing
        # this in a deferred command causes it to occur after all widgets' sizes
        # have been computed by the browser.

        # FIXME - need implementation#
        #     DeferredCommand.add(onWindowResized(Window.getClientWidth(), Window.getClientHeight()))

        self.onWindowResized(Window.getClientWidth(), Window.getClientHeight())

    def onWindowResized(self, width, height):
        # Adjust the shortcut panel and detail area to take up the available room
        # in the window.
        #Logger("Window resized", "width: " + width+ ", height: " + height)

        shortcutHeight = height - self.shortcuts.getAbsoluteTop() - 8
        if (shortcutHeight < 1):
            shortcutHeight = 1
        self.shortcuts.setHeight("" + shortcutHeight)

        # Give the mail detail widget a chance to resize itself as well.
        self.mailDetail.adjustSize(width, height)

    def displayItem(self, item):
        self.mailDetail.setItem(item)

