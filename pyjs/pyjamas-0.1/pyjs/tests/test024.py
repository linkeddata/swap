class CalendarProvider:

    def pushResults(self, acceptor, startRow, people):
        rows = []
        for person in people:
            rows.append((person.getName(), person.getDescription(), person.getSchedule(daysFilter)))
        acceptor.accept(startRow, rows)
