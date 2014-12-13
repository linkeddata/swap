from ui import Grid

class Logger(Grid):
    def __init__(self, target="", message=""):
        if message:
            return Logger().write(target, message)
            
        # make sure there is only one instance of this class
        if _logger: return _logger
        self.setSingleton()

        Grid.__init__(self)

        self.targets=[]
        self.targets.append("app")
        #self.targets.append("ui")
        self.resize(len(self.targets)+1, 2)
        self.setBorderWidth(1)
        self.counter=0
        
        self.setHTML(0, 0, "<b>Log</b>")
        self.setText(1, 0, "app")
        for i in range(len(self.targets)):
            target=self.targets[i]
            self.setText(i+1, 0, target)

    def setSingleton(self):
        """
        _logger=this;
        };
        var _logger=null;
        {
        """
    
    def addTarget(self, target):
        self.targets.append(target)
        self.resize(len(self.targets)+1, 2)
        self.setText(len(self.targets), 0, target)
        return self.targets.index(target)
        
    def write(self, target, message):
        self.counter+=1
        
        if target=='':
            target='app'
        target_idx=self.targets.index(target)
        
        # add new target
        if target_idx<0:
            target_idx=self.addTarget(target)
        
        target_row=target_idx+1     
        old_text=self.getHTML(target_row, 1)
        log_line=self.counter + ": " + message

        if old_text=='&nbsp;':
            new_text=log_line            
        else:
            new_text=old_text + "<br>" + log_line
        self.setHTML(target_row, 1, new_text) 

