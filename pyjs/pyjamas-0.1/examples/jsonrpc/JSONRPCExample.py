from ui import RootPanel, TextArea, Label, Button, HTML, VerticalPanel, HorizontalPanel
from JSONService import JSONProxy

class JSONRPCExample:
    def onModuleLoad(self):
        self.TEXT_WAITING = "Waiting for response..."
        self.TEXT_ERROR = "Server Error"

        self.remote_php = EchoServicePHP()
        self.remote_py = EchoServicePython()

        self.status=Label()
        self.text_area = TextArea()
        self.text_area.setText(r"{'Test'} [\"String\"]")
        self.text_area.setCharacterWidth(80)
        self.text_area.setVisibleLines(8)
        
        self.button_php = Button("Send to PHP Service", self)
        self.button_py = Button("Send to Python Service", self)

        buttons = HorizontalPanel()
        buttons.add(self.button_php)
        buttons.add(self.button_py)
        buttons.setSpacing(8)
        
        info = r"<h2>JSON-RPC Example</h2><p>This example demonstrates the calling of server services with <a href=\"http://json-rpc.org/\">JSON-RPC</a>."
        info += "<p>Enter some text below, and press a button to send the text to an Echo service on your server. An echo service simply sends the exact same text back that it receives."
        
        panel = VerticalPanel()
        panel.add(HTML(info))
        panel.add(self.text_area)
        panel.add(buttons)
        panel.add(self.status)
        
        RootPanel().add(panel)

    def onClick(self, sender):
        self.status.setText(self.TEXT_WAITING)

        if sender == self.button_php:
            id = self.remote_php.echo(self.text_area.getText(), self)
        else:
            id = self.remote_py.echo(self.text_area.getText(), self)
        if id<0:
            self.status.setText(self.TEXT_ERROR)


    def onRemoteResponse(self, response, request_info):
        self.status.setText(response)

    def onRemoteError(self, code, message, request_info):
        self.status.setText("Server Error or Invalid Response: ERROR " + code + " - " + message)


class EchoServicePHP(JSONProxy):
    def __init__(self):
        JSONProxy.__init__(self, "services/EchoService.php", ["echo"])


class EchoServicePython(JSONProxy):
    def __init__(self):
        JSONProxy.__init__(self, "services/EchoService.py", ["echo"])


