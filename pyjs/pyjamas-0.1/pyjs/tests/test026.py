class SchoolCalendarWidget:
    def setDayIncluded(self, day, included):
        if (self.daysFilter[day] == included):
            return
        self.daysFilter[day] = included
