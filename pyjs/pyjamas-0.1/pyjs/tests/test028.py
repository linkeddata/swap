class RowDataAcceptorImpl:

    def accept(self, startRow, data):
        destRowCount = getDataRowCount()
        destColCount = grid.getCellCount(0)
        
        srcRowIndex = 0
        srcRowCount = 5
        destRowIndex = 1
        
        while srcRowIndex < srcRowCount:
            
            srcRowData = data[srcRowIndex]
            
            for srcColIndex in range(destColCount):
                cellHTML = srcRowData[srcColIndex]
                grid.setText(destRowIndex, srcColIndex, cellHTML)
            
            srcRowIndex += 1
            destRowIndex += 1
        
        isLastPage = False
        
        while destRowIndex < destRowCount + 1:
        
            isLastPage = True
            
            for destColIndex in range(destColCount):
                grid.clearCell(destRowIndex, destColIndex)
        
            destRowIndex += 1
            
        navbar.gotoNet.setEnabled(not isLstPage)
        navbar.gotoFirst.setEnabled(startRow > 0)
        navbar.gotoPrev.setEnabled(startRow > 0)
        
        setStatusText((startRow + 1) + " - " + (startRow + srcRowCount))
