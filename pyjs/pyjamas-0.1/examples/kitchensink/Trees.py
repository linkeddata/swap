from Sink import Sink, SinkInfo
from ui import Tree, TreeItem

class Trees(Sink):
    def __init__(self):
        self.fProto = [
            Proto("Beethoven", [
                Proto("Concertos", [
                    Proto("No. 1 - C"), 
                    Proto("No. 2 - B-Flat Major"), 
                    Proto("No. 3 - C Minor"), 
                    Proto("No. 4 - G Major"), 
                    Proto("No. 5 - E-Flat Major")
                ]),
                Proto("Quartets", [
                    Proto("Six String Quartets"), 
                    Proto("Three String Quartets"), 
                    Proto("Grosse Fugue for String Quartets")
                ]),
                Proto("Sonatas", [
                    Proto("Sonata in A Minor"), 
                    Proto("Sonata in F Major")
                ]),
                Proto("Symphonies", [
                    Proto("No. 1 - C Major"), 
                    Proto("No. 2 - D Major"), 
                    Proto("No. 3 - E-Flat Major"), 
                    Proto("No. 4 - B-Flat Major"), 
                    Proto("No. 5 - C Minor"), 
                    Proto("No. 6 - F Major"), 
                    Proto("No. 7 - A Major"), 
                    Proto("No. 8 - F Major"), 
                    Proto("No. 9 - D Minor")
                ])
            ]),
        
            Proto("Brahms", [
                Proto("Concertos", [
                    Proto("Violin Concerto"),
                    Proto("Double Concerto - A Minor"),
                    Proto("Piano Concerto No. 1 - D Minor"),
                    Proto("Piano Concerto No. 2 - B-Flat Major")
                ]),
                Proto("Quartets", [
                    Proto("Piano Quartet No. 1 - G Minor"),
                    Proto("Piano Quartet No. 2 - A Major"),
                    Proto("Piano Quartet No. 3 - C Minor"),
                    Proto("String Quartet No. 3 - B-Flat Minor")
                ]),
                Proto("Sonatas", [
                    Proto("Two Sonatas for Clarinet - F Minor"),
                    Proto("Two Sonatas for Clarinet - E-Flat Major")
                ]),
                Proto("Symphonies", [
                    Proto("No. 1 - C Minor"),
                    Proto("No. 2 - D Minor"),
                    Proto("No. 3 - F Major"),
                    Proto("No. 4 - E Minor")
                ])      
            ]),
        
            Proto("Mozart", [
                Proto("Concertos", [
                    Proto("Piano Concerto No. 12"),
                    Proto("Piano Concerto No. 17"),
                    Proto("Clarinet Concerto"),
                    Proto("Violin Concerto No. 5"),
                    Proto("Violin Concerto No. 4")
                ]),
            ])
        ]

        self.fTree = Tree()
        
        for i in range(len(self.fProto)):
            self.createItem(self.fProto[i])
            self.fTree.addItem(self.fProto[i].item)
        
        self.fTree.addTreeListener(self)
        self.setWidget(self.fTree)
        
    def onTreeItemSelected(self, item):
        pass
    
    def onTreeItemStateChanged(self, item):
        child = item.getChild(0)
        if hasattr(child, "isPendingItem"):
            item.removeItem(child)
        
            proto = item.getUserObject()
            for i in range(len(proto.children)):
                self.createItem(proto.children[i])
                item.addItem(proto.children[i].item)

    def createItem(self, proto):
        proto.item = TreeItem(proto.text)
        proto.item.setUserObject(proto)
        if len(proto.children) > 0:
            proto.item.addItem(PendingItem())


class Proto:
    def __init__(self, text, children=None):
        self.children = []
        self.item = None
        self.text = text
        
        if children != None:
            self.children = children


class PendingItem(TreeItem):
    def __init__(self):
        TreeItem.__init__(self, "Please wait...")

    def isPendingItem(self):
        return True


def init():
    text="GWT has a built-in <code>Tree</code> widget. The tree is focusable and has keyboard support as well."
    return SinkInfo("Trees", text, Trees)
