from UnitTest import UnitTest

class StringTest(UnitTest):
	def __init__(self):
		UnitTest.__init__(self)

	def getName(self):
		return "String"

	def testReplace(self):
		text="this is a rather long string"
		expected_result1="th--- --- a rather long string"
		expected_result2="thi-- is a rather long string"
		expected_result3="this_is_a_rather_long_string"
		
		result=text.replace("is", "---")
		self.assertEquals(result, expected_result1)

		result=text.replace("s", "--", 1)
		self.assertEquals(result, expected_result2)

		result=text.replace(" ", "_")
		self.assertEquals(result, expected_result3)
		
	def testFind(self):
		text="this is a rather long string"

		result=text.find("not found")
		self.assertEquals(result, -1)

		result=text.find("is")
		self.assertEquals(result, 2)
		
		result=text.find("is", 3)
		self.assertEquals(result, 5)
		
		result=text.find("is", 2, 3)
		self.assertEquals(result, -1)

	def testJoin(self):
		data="this is a rather long string"
		data=data.split(" ")
		sep1=", "
		sep2=""
		expected_result1="this, is, a, rather, long, string"
		expected_result2="thisisaratherlongstring"
		
		result=sep1.join(data)
		self.assertEquals(result, expected_result1)
		
		result=sep2.join(data)
		self.assertEquals(result, expected_result2)

	def testSplit(self):
		text=" this is  a rather long string  "
		space=" "
		empty=""
		expected_result1=" this is  a rather long string "
		expected_result2="thisis  a rather long string  "
		expected_result3="this is a rather long string"
		
		result=space.join(text.split(space))
		self.assertEquals(result, expected_result1)
		
		result=empty.join(text.split(space, 2))
		self.assertEquals(result, expected_result2)
		
		result=space.join(text.split())
		self.assertEquals(result, expected_result3)
		
		result=empty.split()
		self.assertEquals(len(result), 0)
		
	def testStrip(self):
		text=" this is  a rather long string  "
		expected_result1="this is  a rather long string"
		expected_result2="a rather long string"
		
		result=text.strip()
		self.assertEquals(result, expected_result1)
		
		result=text.strip(" sthi")
		self.assertEquals(result, expected_result2)

		
		
		
		