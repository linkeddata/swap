from UnitTest import UnitTest

class ClassTest(UnitTest):
	def __init__(self):
		UnitTest.__init__(self)

	def getName(self):
		return "Class"

	# test Class.x
	def testClassVars(self):
		expected_result1="test"
		expected_result2=1
		
		# check class var value without instance
		self.assertEquals(ExampleClass.x, expected_result1)
		
		# verify class var value for instances
		y = ExampleClass()
		self.assertEquals(y.x, expected_result1)
		
		# modify class var
		ExampleClass.x = expected_result2
		self.assertEquals(ExampleClass.x, expected_result2)
		
		# verify that class var changed for NEW instances
		z = ExampleClass()
		self.assertEquals(z.x, expected_result2)
		
		# verify that class var changed for EXISTING instances
		self.assertEquals(y.x, expected_result2)

	# test Class().x
	def testInheritedProperties(self):
		expected_result1="test"
		expected_result2=1
		expected_result3="other"

		# check parent property
		obj1 = ExampleParentClass()
		self.assertEquals(obj1.x, expected_result1)

		# check default inherited property
		obj1.x = expected_result2
		obj2 = ExampleChildClass()
		self.assertEquals(obj2.x, expected_result1)

		# change inherited property
		obj2.x = expected_result3
		self.assertEquals(obj2.x, expected_result3)

		# verify that parent class properties were NOT changed
		self.assertEquals(obj1.x, expected_result2)

	# test Class().anObject
	def testInheritedPropertyObjects(self):
		expected_result1 = "another"
		expected_result2 = "other"

		# check parent property
		obj1 = ExampleParentObject()
		self.assertEquals(len(obj1.x), 0)

		# check default inherited property
		obj1.x.append(expected_result2)
		
		obj2 = ExampleChildObject()
		self.assertEquals(len(obj2.x), 1)

		# change inherited property
		obj2.x.append(expected_result1)
		self.assertEquals(obj2.x[1], expected_result1)

		# verify that parent class properties were NOT changed
		self.assertEquals(obj1.x[0], expected_result2)

	# test Class().__init__
	def testInheritedConstructors(self):
		expected_result1 = "test"
		expected_result2 = "parent"
		expected_result3 = "grandparent"
		expected_result4 = "older"

		# verify that parent.__init__ is called if there is no child.__init__()
		obj1 = ExampleChildNoConstructor()
		self.assertEquals(obj1.x, expected_result1, "ExampleParentConstructor.__init__() was NOT called")

		# verify that parent.__init__ is NOT called (child.__init__() is defined)
		obj2 = ExampleChildConstructor()
		self.assertNotEqual(obj2.x, expected_result1, "ExampleParentConstructor.__init__() was called")

		# verify that parent.__init__ is explicitly called
		obj3 = ExampleChildExplicitConstructor()
		self.assertEquals(obj3.x, expected_result1, "ExampleParentConstructor.__init__() was NOT called")

		# verify inherited values
		self.assertEquals(obj1.y, expected_result2, "Did not inherit property from parent")
		self.assertEquals(obj2.y, expected_result2, "Did not inherit property from parent")
		self.assertEquals(obj1.z, expected_result3, "Did not inherit property from grandparent")
		self.assertEquals(obj2.z, expected_result3, "Did not inherit property from grandparent")
		
		self.assertNotEqual(obj1.r, expected_result4, "ExampleGrandParentConstructor.__init__() was called")
		self.assertNotEqual(obj2.r, expected_result4, "ExampleGrandParentConstructor.__init__() was called")

		# check inherited class vars (from parent)
		self.assertEqual(ExampleChildConstructor.y, expected_result2, "Did not inherit class var from parent")
		self.assertEqual(ExampleChildNoConstructor.y, expected_result2, "Did not inherit class var from parent")
		self.assertEqual(ExampleChildExplicitConstructor.y, expected_result2, "Did not inherit class var from parent")

		# check inherited class vars (from grandparent)
		self.assertEqual(ExampleChildConstructor.z, expected_result3, "Did not inherit class var from grandparent")
		self.assertEqual(ExampleChildNoConstructor.z, expected_result3, "Did not inherit class var from grandparent")
		self.assertEqual(ExampleChildExplicitConstructor.z, expected_result3, "Did not inherit class var from grandparent")



# testClassVars
class ExampleClass:
	x = "test"


# testInheritedProperties
class ExampleParentClass:
	x = "test"

class ExampleChildClass(ExampleParentClass):
	pass


# testInheritedPropertyObjects
class ExampleParentObject:
	x = []

class ExampleChildObject(ExampleParentObject):
	pass


# testInheritedConstructors
class ExampleGrandParentConstructor:
	z = "grandparent"

	def __init__(self):
		self.r = "older"

	def older(self):
		self.w = 2

class ExampleParentConstructor(ExampleGrandParentConstructor):
	y = "parent"

	def __init__(self):
		self.x = "test"

	def dosomething(self):
		self.m = 1

class ExampleChildConstructor(ExampleParentConstructor):
	def __init__(self):
		pass

class ExampleChildNoConstructor(ExampleParentConstructor):
	pass

class ExampleChildExplicitConstructor(ExampleParentConstructor):
	def __init__(self):
		ExampleParentConstructor.__init__(self)



