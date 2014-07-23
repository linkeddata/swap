from Sink import Sink, SinkInfo
from ui import MenuBar, MenuItem
import Window

class Menus(Sink):
    def __init__(self):
        self.menu = MenuBar()
        
        subMenu = MenuBar(True)
        subMenu.addNewItem("<code>Code</code>", True, None, self)
        subMenu.addNewItem("<strike>Strikethrough</strike>", True, None, self)
        subMenu.addNewItem("<u>Underlined</u>", True, None, self)
        
        menu0 = MenuBar(True)
        menu0.addNewItem("<b>Bold</b>", True, None, self)
        menu0.addNewItem("<i>Italicized</i>", True, None, self)
        menu0.addNewItem("More &#187;", True, None, subMenu)
        menu1 = MenuBar(True)
        menu1.addNewItem("<font color='#FF0000'><b>Apple</b></font>", True, None, self)
        menu1.addNewItem("<font color='#FFFF00'><b>Banana</b></font>", True, None, self)
        menu1.addNewItem("<font color='#FFFFFF'><b>Coconut</b></font>", True, None, self)
        menu1.addNewItem("<font color='#8B4513'><b>Donut</b></font>", True, None, self)
        menu2 = MenuBar(True)
        menu2.addNewItem("Bling", False, None, self)
        menu2.addNewItem("Ginormous", False, None, self)
        menu2.addNewItem("<code>w00t!</code>", True, True, self)
        
        self.menu.addItem(MenuItem("Style", False, None, menu0))
        self.menu.addItem(MenuItem("Fruit", False, None, menu1))
        self.menu.addItem(MenuItem("Term", False, None, menu2))
        
        self.menu.setWidth("100%")
        
        self.setWidget(self.menu)


    def execute(self):
        Window.alert("Thank you for selecting a menu item.")
        
    def onShow(self):
        pass


def init():
    return SinkInfo("Menus", "The GWT <code>MenuBar</code> class makes it easy to build menus, including cascading sub-menus.", Menus)