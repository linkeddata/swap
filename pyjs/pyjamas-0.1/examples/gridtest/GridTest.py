from ui import Button, RootPanel
from ui import Label, Grid, CellFormatter, RowFormatter
from ui import HTMLTable, CheckBox
import Window


class GridTest:
	def onModuleLoad(self):
		self.page=0
		self.min_page=1
		self.max_page=10
		
		self.add=Button("Next >", self)
		self.sub=Button("< Prev", self)
		
		self.g=Grid()
		self.g.resize(5, 5)
		self.g.setHTML(0, 0, "<b>Grid Test</b>")
		self.g.setBorderWidth(2)
		self.g.setCellPadding(4)
		self.g.setCellSpacing(1)
		
		self.updatePageDisplay()
		RootPanel().add(self.sub)
		RootPanel().add(self.add)
		RootPanel().add(self.g)

	def onClick(self, sender):
		if sender==self.add:
			self.page+=1
		elif sender==self.sub:
			self.page-=1
		self.updatePageDisplay()
		

	def updatePageDisplay(self):
		if self.page<self.min_page: self.page=self.min_page
		elif self.page>self.max_page: self.page=self.max_page
		total_pages=(self.max_page-self.min_page) + 1
		
		self.g.setHTML(0, 4, "<b>page " + self.page + ' of ' + total_pages + "</b>")
		
		if self.page>=self.max_page:
			self.add.setEnabled(False)
		else:
			self.add.setEnabled(True)
			
		if self.page<=self.min_page:
			self.sub.setEnabled(False)
		else:
			self.sub.setEnabled(True)

		for y in range(1, 5):
			for x in range(5):
				self.g.setText(y, x, self.page + ' (' + y + ',' + x + ')')




