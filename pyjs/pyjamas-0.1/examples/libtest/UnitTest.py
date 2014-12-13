from write import write, writebr

class UnitTest:
	def __init__(self):
		self.tests_completed=0
		self.tests_failed=0
		self.tests_passed=0
		self.test_methods=[]
		
		# define alternate names for methods
		self.assertEqual = self.failUnlessEqual
		self.assertEquals = self.failUnlessEqual

		self.assertNotEqual = self.failIfEqual
		self.assertFalse = self.failIf
		self.assertTrue = self.failUnless

	def run(self):
		self.getTestMethods()
		for test_method_name in self.test_methods:
			test_method=getattr(self, test_method_name)
			self.setUp()
			test_method()
			self.tearDown()
		
		self.displayStats()
		
	def setUp(self):
		pass
		
	def tearDown(self):
		pass
	
	def getName(self):
		return ""

	def getNameFmt(self, msg=""):
		if self.getName():
			if msg:
				msg=" " + msg
			return self.getName() + msg + ": "
		return ""
		
	def getTestMethods(self):
		self.test_methods=filter(self, self.isTestMethod, dir(self))
		
	def isTestMethod(self, method):
		if callable(getattr(self, method)):
			if method.find("test")==0:
				return True
		return False

	def fail(self, msg=None):
		self.tests_failed+=1
		
		if not msg:
			msg="assertion failed"

		title="<b>" + self.getNameFmt("Test failed") + "</b>"
		writebr(title + msg)
		return False

	def startTest(self):
		self.tests_completed+=1

	def failIf(self, expr, msg=None):
		self.startTest()
		if expr:
			return self.fail(msg)

	def failUnless(self, expr, msg=None):
		self.startTest()
		if not expr:
			return self.fail(msg)

	def failUnlessEqual(self, first, second, msg=None):
		self.startTest()
		if not first == second:
			if not msg:
				msg=str(first) + " != " + str(second)
			return self.fail(msg)

	def failIfEqual(self, first, second, msg=None):
		self.startTest()
		if first == second:
			if not msg:
				msg=str(first) + " == " + str(second)
			return self.fail(msg)

	def failUnlessAlmostEqual(self, first, second, places=7, msg=None):
		self.startTest()
		if round(second-first, places) != 0:
			if not msg:
				msg=str(first) + " != " + str(second) + " within " + str(places) + " places"
			return self.fail(msg)

	def failIfAlmostEqual(self, first, second, places=7, msg=None):
		self.startTest()
		if round(second-first, places) == 0:
			if not msg:
				msg=str(first) + " == " + str(second) + " within " + str(places) + " places"
			return self.fail(msg)

	def displayStats(self):
		if self.tests_failed:
			bg_colour="#ff0000"
			fg_colour="#ffffff"
		else:
			bg_colour="#00ff00"
			fg_colour="#000000"
		
		tests_passed=self.tests_completed - self.tests_failed
		
		output="<table cellpadding=4 width=100%><tr><td bgcolor='" + bg_colour + "'><font face='arial' size=4 color='" + fg_colour + "'><b>"
		output+=self.getNameFmt() + "Passed " + tests_passed + "/" + self.tests_completed + " tests"
		
		if self.tests_failed:
			output+=" (" + self.tests_failed + " failed)"
			
		output+="</b></font></td></tr></table>"
		
		write(output)

