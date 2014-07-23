import math

class TimeSlot:
    def __init__(self, dayOfWeek, startMinutes, endMinutes):
        self.DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        self.dayOfWeek = dayOfWeek
        self.startMinutes = startMinutes
        self.endMinutes = endMinutes
    
    def compareTo(self, other):
        if self.dayOfWeek < other.dayOfWeek:
            return -1
        elif self.dayOfWeek > other.dayOfWeek:
            return 1
        else:
            if self.startMinutes < other.startMinutes:
                return -1
            elif self.startMinutes > other.startMinutes:
                return 1
        return 0

    def getDayOfWeek(self):
        return self.dayOfWeek

    def getDescription(self):
        return self.DAYS[self.dayOfWeek] + " " + self.getHrsMins(self.startMinutes) + "-" + self.getHrsMins(self.endMinutes)
        
    def getHrsMins(self, mins):
        hrs = math.floor(mins / 60)
        if hrs > 12:
            hrs -= 12
        remainder = math.floor(mins % 60)
        if remainder < 10:
            string_mins = "0" + str(remainder)
        else:
            string_mins = str(remainder)
        return str(hrs) + ":" + string_mins

