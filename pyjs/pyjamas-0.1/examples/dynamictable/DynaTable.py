from ui import RootPanel
from DayFilterWidget import DayFilterWidget
from SchoolCalendarWidget import SchoolCalendarWidget

class DynaTable:

    def onModuleLoad(self):
        slot = RootPanel("calendar")
        if slot:
            calendar = SchoolCalendarWidget(15)
            slot.add(calendar)
            
            slot = RootPanel("days")
            if slot:
                filterWidget = DayFilterWidget(calendar)
                slot.add(filterWidget)
