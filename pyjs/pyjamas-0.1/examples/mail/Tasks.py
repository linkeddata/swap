from ui import CheckBox, Composite, VerticalPanel

class Tasks(Composite):

    def __init__(self):
        panel = VerticalPanel()
        panel.add(CheckBox("Get groceries"))
        panel.add(CheckBox("Walk the dog"))
        panel.add(CheckBox("Start Web 2.0 company"))
        panel.add(CheckBox("Write cool app in GWT"))
        panel.add(CheckBox("Get funding"))
        panel.add(CheckBox("Take a vacation"))
        self.setWidget(panel)
        self.setStyleName("mail-Tasks")
