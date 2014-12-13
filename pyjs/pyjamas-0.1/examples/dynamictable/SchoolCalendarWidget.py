from ui import Composite
from DeferredCommand import DeferredCommand
from SchoolCalendarService import SchoolCalendarService
from DynaTableWidget import DynaTableWidget
from Person import Person
from Student import Student
from Professor import Professor

class CalendarProvider:

    def __init__(self, owner):
        self.owner = owner
        self.calService = SchoolCalendarService()
        self.lastStartRow = -1
        self.lastMaxRows = -1
        self.lastPeople = []
        
    def updateRowData(self, startRow, maxRows, acceptor):
        if startRow == self.lastStartRow:
            if maxRows == self.lastMaxRows:
                self.pushResults(acceptor, startRow, self.lastPeople)
                return
        
        self.calService.getPeople(startRow, maxRows, CalendarProviderHandler(self, acceptor, startRow, maxRows))

    def pushResults(self, acceptor, startRow, people):
        rows = []
        for person in people:
            rows.append([person.getName(), person.getDescription(), person.getSchedule(self.owner.daysFilter)])
        acceptor.accept(startRow, rows)


class CalendarProviderHandler:
    def __init__(self, owner, acceptor, startRow, maxRows):
        self.owner = owner
        self.acceptor = acceptor
        self.startRow = startRow
        self.maxRows = maxRows
    
    def onRemoteResponse(self, response, requestInfo):
        people = response
        
        self.owner.lastStartRow = self.startRow
        self.owner.lastMaxRows = self.maxRows
        self.owner.lastPeople = people
        self.owner.pushResults(self.acceptor, self.startRow, people)
        
    def onRemoteError(self, code, message, request):
        self.acceptor.failed(message)
    

class SchoolCalendarWidget(Composite):
    
    def __init__(self, visibleRows):
        Composite.__init__(self)
    
        columns = ["Name", "Description", "Schedule"]
        styles = ["name", "desc", "sched"]
        self.calProvider = CalendarProvider(self)
        self.daysFilter = [True, True, True, True, True, True, True]
        self.pendingRefresh = False

        self.dynaTable = DynaTableWidget(self.calProvider, columns, styles, visibleRows)
        self.setWidget(self.dynaTable)
        
    def getDayIncluded(self, day):
        return self.daysFilter[day]
        
    def onLoad(self):
        self.dynaTable.refresh()

    def setDayIncluded(self, day, included):
        if (self.daysFilter[day] == included):
            return

        self.daysFilter[day] = included
        
        if not self.pendingRefresh:
            self.pendingRefresh = True
            DeferredCommand().add(self)

    def execute(self):
        self.pendingRefresh = False
        self.dynaTable.refresh()
