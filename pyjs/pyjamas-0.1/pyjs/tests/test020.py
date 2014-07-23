import ui

class DayCheckBox(ui.CheckBox):
    def __init__(self, caption, day):
        ui.CheckBox.__init__(self, caption)
        self.day = day
