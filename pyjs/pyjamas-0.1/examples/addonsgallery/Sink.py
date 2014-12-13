from ui import Composite

class Sink(Composite):
    def __init__(self):
        pass
    
    def onHide(self):
        pass
        
    def onShow(self):
        pass

    def baseURL(self):
        return "http://code.google.com/webtoolkit/documentation/examples/kitchensink/"

class SinkInfo:
    def __init__(self, name, desc, object_type):
        self.name=name
        self.description=desc
        self.object_type=object_type
        self.instance=None

    def createInstance(self):
        return self.object_type()

    def getDescription(self):
        return self.description

    def getInstance(self):
        if self.instance==None:
            self.instance=self.createInstance()
        return self.instance
    
    def getName(self):
        return self.name
    
