class Schedule:

    def __init__(self):
        self.timeSlots = []

    def addTimeSlot(self, timeSlot):
        self.timeSlots.append(timeSlot)
        
    def getDescription(self, daysFilter):
        s = None
        for timeSlot in self.timeSlots:
            if daysFilter[timeSlot.dayOfWeek]:
                if not s:
                    s = timeSlot.getDescription()
                else:
                    s += ", " + timeSlot.getDescription()
        if s:
            return s
        else:
            return ""
