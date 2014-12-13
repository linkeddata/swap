class TimeSlot:

    def getDescription(self):
        return self.getHrsMins(self.startMinutes) + "-" + self.getHrsMins(self.endMinutes)
