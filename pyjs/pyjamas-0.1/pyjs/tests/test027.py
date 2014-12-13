class RowDataAcceptorImpl:

    def accept(self, startRow, data):
        srcRowIndex = 0
        srcRowCount = 5
        destRowIndex = 1
        
        while srcRowIndex < srcRowCount:
            srcRowIndex += 1
            destRowIndex += 1
