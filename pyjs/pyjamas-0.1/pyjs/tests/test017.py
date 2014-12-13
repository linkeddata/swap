class TimeSlot:

    DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    def getDescription(self):
        return self.DAYS[self.dayOfWeek] + " " + self.getHrsMins(self.startMinutes) + "-" + self.getHrsMins(self.endMinutes)

    def getHrsMins(self, mins):
        pass