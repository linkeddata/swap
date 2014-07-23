from StringTest import StringTest
from ListTest import ListTest
from ClassTest import ClassTest

class LibTest:	
	def onModuleLoad(self):
		ClassTest().run()
		StringTest().run()
		ListTest().run()


