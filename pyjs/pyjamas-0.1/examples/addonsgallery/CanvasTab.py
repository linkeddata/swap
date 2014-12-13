from Sink import Sink, SinkInfo
from ui import Image, HTML, VerticalPanel, HorizontalPanel
from Canvas import Canvas, CanvasImage, ImageLoadListener
from Timer import Timer
import math

class CanvasTab(Sink):
    def __init__(self):
        colour_grid = ColourGridCanvas()
        rotated = RotatedCanvas()       
        spheres = SpheresCanvas()
        pattern = PatternCanvas()
        spiro = SpiroCanvas()
        self.solar = SolarCanvas()
        
        row0 = HorizontalPanel()
        row0.setSpacing(8)
        row0.add(colour_grid)
        row0.add(rotated)
        row0.add(spheres)
        row0.add(pattern)
        
        row1 = HorizontalPanel()
        row1.setSpacing(8)
        row1.add(self.solar)
        row1.add(spiro)

        panel = VerticalPanel()
        panel.add(row0)
        panel.add(row1)

        self.setWidget(panel)

    def onShow(self):
        self.solar.isActive = True
        self.solar.onTimer()
    
    def onHide(self):
        self.solar.isActive = False


def init():
    text=r"<b>Canvas vector drawing component</b><p>Gives python access to the browser's native canvas tag (<a href=\"http://excanvas.sourceforge.net\">Explorer Canvas</a> in IE)"
    text+=r"<p>Originally by Alexei Sokolov at <a href=\"http://gwt.components.googlepages.com\">gwt.components.googlepages.com</a>"
    text+=r"<br>Samples ported from the <a href=\"http://developer.mozilla.org/en/docs/Canvas_tutorial\">Mozilla canvas tutorial</a>" 
    
    return SinkInfo("Canvas", text, CanvasTab)


class ColourGridCanvas(Canvas):
    def __init__(self):
        Canvas.__init__(self, 150, 150)
        self.draw()
        
    def draw(self):
        for i in range(0, 6):
            for j in range(0, 6):
                self.context.fillStyle = 'rgb(' + math.floor(255-42.5*i) + ',' + math.floor(255-42.5*j) + ',0)'
                self.context.fillRect(j*25,i*25,25,25)


class RotatedCanvas(Canvas):
    def __init__(self):
        Canvas.__init__(self, 150, 150)
        self.context.translate(75,75)
        self.draw()
        
    def draw(self):
        # Loop through rings (from inside to out)
        for i in range(1,6):
            self.context.save()
            self.context.fillStyle = 'rgb('+(51*i)+','+(255-51*i)+',255)'
        
            # draw individual dots
            for j in range(0,i*6): 
                self.context.rotate(math.pi*2/(i*6))
                self.context.beginPath()
                self.context.arc(0,i*12.5,5,0,math.pi*2,True)
                self.context.fill()
        
            self.context.restore()


class SpheresCanvas(Canvas):
    def __init__(self):
        Canvas.__init__(self, 150, 150)
        self.draw()
        
    def draw(self):
        # create gradients
        radgrad = self.context.createRadialGradient(45,45,10,52,50,30)
        radgrad.addColorStop(0, '#A7D30C')
        radgrad.addColorStop(0.9, '#019F62')
        radgrad.addColorStop(1, 'rgba(1,159,98,0)')
  
        radgrad2 = self.context.createRadialGradient(105,105,20,112,120,50)
        radgrad2.addColorStop(0, '#FF5F98')
        radgrad2.addColorStop(0.75, '#FF0188')
        radgrad2.addColorStop(1, 'rgba(255,1,136,0)')

        radgrad3 = self.context.createRadialGradient(95,15,15,102,20,40)
        radgrad3.addColorStop(0, '#00C9FF')
        radgrad3.addColorStop(0.8, '#00B5E2')
        radgrad3.addColorStop(1, 'rgba(0,201,255,0)')

        radgrad4 = self.context.createRadialGradient(0,150,50,0,140,90)
        radgrad4.addColorStop(0, '#F4F201')
        radgrad4.addColorStop(0.8, '#E4C700')
        radgrad4.addColorStop(1, 'rgba(228,199,0,0)')
 
        # draw shapes
        self.context.fillStyle = radgrad4
        self.context.fillRect(0,0,150,150)
        self.context.fillStyle = radgrad3
        self.context.fillRect(0,0,150,150)
        self.context.fillStyle = radgrad2
        self.context.fillRect(0,0,150,150)
        self.context.fillStyle = radgrad
        self.context.fillRect(0,0,150,150)


class PatternCanvas(Canvas):
    def __init__(self):
        Canvas.__init__(self, 150, 150)
        self.img = CanvasImage('images/wallpaper.png', self)

    def onLoad(self, sender):
        if sender==self.img:
            self.draw()
    
    def onError(self):
        pass

    def draw(self):
        ptrn = self.context.createPattern(self.img, 'repeat')
        self.context.fillStyle = ptrn
        self.context.fillRect(0,0,200,200)


class SpiroCanvas(Canvas):
    def __init__(self):
        Canvas.__init__(self, 300, 300)
        self.draw()     

    def draw(self):
        self.context.fillRect(0,0,300,300)
        for i in range(0, 3):
            for j in range(0, 3):
                self.context.save()
                self.context.strokeStyle = "#9CFF00"
                self.context.translate(50+j*100,50+i*100)
                self.drawSpirograph(20*(j+2)/(j+1),-8*(i+3)/(i+1),10)
                self.context.restore()

    def drawSpirograph(self, R, r, O):
        x1 = R-O
        y1 = 0
        i  = 1
        self.context.beginPath()
        self.context.moveTo(x1,y1)
        while x2 != R-O and y2 != 0:
            if i>20000:
                break
            x2 = (R+r)*math.cos(i*math.pi/72) - (r+O)*math.cos(((R+r)/r)*(i*math.pi/72))
            y2 = (R+r)*math.sin(i*math.pi/72) - (r+O)*math.sin(((R+r)/r)*(i*math.pi/72))
            self.context.lineTo(x2,y2)
            x1 = x2
            y1 = y2
            i+=1
        self.context.stroke()


class SolarCanvas(Canvas):
    def __init__(self):
        Canvas.__init__(self, 300, 300)     
        self.sun = CanvasImage('images/sun.png')
        self.moon = CanvasImage('images/moon.png')
        self.earth = CanvasImage('images/earth.png')
        
        self.loader = ImageLoadListener()
        self.loader.add(self.sun)
        self.loader.add(self.moon)
        self.loader.add(self.earth) 
        
        self.isActive = True
        self.onTimer()

    def onTimer(self):
        if not self.isActive:
            return
        
        Timer(100, self)
        self.draw()

    def getTimeSeconds(self):
        """
        var x = new Date();
        return x.getSeconds();
        """

    def getTimeMilliseconds(self):
        """
        var x = new Date();
        return x.getMilliseconds();
        """

    def draw(self):
        if not self.loader.isLoaded():
            return
        
        self.context.globalCompositeOperation = 'destination-over'

        # clear canvas
        self.context.clearRect(0,0,300,300) 
        
        self.context.save()
        self.context.fillStyle = 'rgba(0,0,0,0.4)'
        self.context.strokeStyle = 'rgba(0,153,255,0.4)'
        self.context.translate(150,150)
        
        # Earth
        self.context.rotate( ((2*math.pi)/60)*self.getTimeSeconds() + ((2*math.pi)/60000)*self.getTimeMilliseconds() )
        self.context.translate(105,0)
        self.context.fillRect(0,-12,50,24) # Shadow
        self.context.drawImage(self.earth,-12,-12)
        
        # Moon
        self.context.save()
        self.context.rotate( ((2*math.pi)/6)*self.getTimeSeconds() + ((2*math.pi)/6000)*self.getTimeMilliseconds() )
        self.context.translate(0,28.5)
        self.context.drawImage(self.moon,-3.5,-3.5)
        self.context.restore()
        
        self.context.restore()
        
        self.context.beginPath()
        self.context.arc(150,150,105,0,math.pi*2,False) # Earth orbit
        self.context.stroke()
        
        self.context.drawImage(self.sun,0,0)

