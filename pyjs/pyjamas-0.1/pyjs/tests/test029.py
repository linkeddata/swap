class DynaTableWidget:
        
    def initTable(self, columns, columnStyles, rowCount):
        self.grid.resize(rowCount + 1, len(columns))
        for i in range(len(columns)):
            caption = columns[i]
            self.grid.setText(0, i, columns[i])