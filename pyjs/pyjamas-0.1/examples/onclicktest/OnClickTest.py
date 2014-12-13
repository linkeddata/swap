from ui import Button, RootPanel
import Window


def onButtonClick(sender):
	Window.alert("function called")


class OnClickTest:
	def onModuleLoad(self):
		self.b = Button("function callback", onButtonClick)
		self.b2 = Button("object callback", self)
		RootPanel().add(self.b)
		RootPanel().add(self.b2)

	def onClick(self, sender):
		Window.alert("object called")




