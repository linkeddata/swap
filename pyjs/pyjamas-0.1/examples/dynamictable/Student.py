from Schedule import Schedule
from Person import Person

class Student(Person):

    def __init__(self):
        self.classSchedule = Schedule()

    def getSchedule(self, daysFilter):
        return self.classSchedule.getDescription(daysFilter)
    
    def getClassSchedule(self):
        return self.classSchedule
