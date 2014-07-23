#Timer().hookWindowClosing()
timers = []

class Timer:
    MAX_PERIOD = 1000 * 60 * 60 * 24 * 365
    MIN_PERIOD = 1
    
    def __init__(self, delay = 0, object = None):
        self.isRepeating = False
        self.timerId = 0

        self.listener = object
        if delay >= Timer.MIN_PERIOD:
            self.schedule(delay)
    
    def clearInterval(self, id):
        """
        $wnd.clearInterval(id);
        """

    def clearTimeout(self, id):
        """
        $wnd.clearTimeout(id);
        """

    def createInterval(self, timer, period):
        """
        return $wnd.setInterval(function() { timer.fire(); }, period);
        """

    def createTimeout(self, timer, delay):
        """
        return $wnd.setTimeout(function() { timer.fire(); }, delay);
        """

    # TODO - requires Window.addWindowCloseListener
    def hookWindowClosing(self):
        pass
    
    def cancel(self):
        global timers
        
        if self.isRepeating:
            self.clearInterval(self.timerId)
        else:
            self.clearTimeout(self.timerId)
        timers.remove(self)

    def run(self):
        if self.listener:
            self.listener.onTimer(self.timerId)
    
    def schedule(self, delayMillis):
        global timers
        
        if delayMillis < Timer.MIN_PERIOD or delayMillis >= Timer.MAX_PERIOD:
            alert("Timer delay must be positive and less than " + Timer.MAX_PERIOD)
        self.cancel()
        self.isRepeating = False
        self.timerId = self.createTimeout(self, delayMillis)
        timers.append(self)

    # TODO: UncaughtExceptionHandler, fireAndCatch
    def fire(self):
        self.fireImpl()

    def fireImpl(self):
        global timers
        
        if not self.isRepeating:
            timers.remove(self)

        self.run()

    def getID(self):
        return self.timerId


    
