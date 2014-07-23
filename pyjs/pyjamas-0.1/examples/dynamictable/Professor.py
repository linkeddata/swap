from Person import Person
from Schedule import Schedule

class Professor(Person):

    def __init__(self):
        self.teachingSchedule = Schedule()
        
    def getSchedule(self, daysFilter):
        return self.teachingSchedule.getDescription(daysFilter)
    
    def getTeachingSchedule(self):
        return self.teachingSchedule
