class TimeSlot:

    def __init__(self, dayOfWeek, startMinutes, endMinutes):
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
