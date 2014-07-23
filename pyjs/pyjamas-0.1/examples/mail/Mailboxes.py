from ui import Composite, Tree, TreeItem

    
class Mailboxes(Composite):
    def __init__(self):
        self.tree = Tree()
        root = TreeItem(self.imageItemHTML("home.gif", "foo@example.com"))
        self.tree.addItem(root)     
        inboxItem = self.addImageItem(root, "Inbox")
        self.addImageItem(root, "Drafts")
        self.addImageItem(root, "Templates")
        self.addImageItem(root, "Sent")
        self.addImageItem(root, "Trash")

        root.setState(True)
        self.setWidget(self.tree)

    def addImageItem(self, root, title):
        item = TreeItem(self.imageItemHTML(title + ".gif", title))
        root.addItem(item)
        return item

    def imageItemHTML(self, imageUrl, title):
        value  = "<span><img style='margin-right:4px' src='"
        value += "http://code.google.com/webtoolkit/documentation/examples/desktopclone/"
        value += imageUrl.toLowerCase() + "'>" + title + "</span>"
        return value
