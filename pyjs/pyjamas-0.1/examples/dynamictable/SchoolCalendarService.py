from JSONService import JSONProxy

class SchoolCalendarService(JSONProxy):
    def __init__(self):
        JSONProxy.__init__(self, "SchoolCalendarService.php", ["getPeople"])
