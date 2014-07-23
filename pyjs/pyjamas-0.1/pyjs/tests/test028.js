function RowDataAcceptorImpl() {
    return new __RowDataAcceptorImpl();
}
function __RowDataAcceptorImpl() {
}
__RowDataAcceptorImpl.prototype.accept = function(startRow, data) {
    var destRowCount = getDataRowCount();
    var destColCount = grid.getCellCount(0);
    var srcRowIndex = 0;
    var srcRowCount = 5;
    var destRowIndex = 1;
    while ((srcRowIndex < srcRowCount)) {
    var srcRowData = data.__getitem__(srcRowIndex);

        var __srcColIndex = pyjslib_range(destColCount).__iter__();
        try {
            while (true) {
                var srcColIndex = __srcColIndex.next();
                
        
    var cellHTML = srcRowData.__getitem__(srcColIndex);
    grid.setText(destRowIndex, srcColIndex, cellHTML);

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }
        
    srcRowIndex += 1;
    destRowIndex += 1;
    }
    var isLastPage = false;
    while ((destRowIndex < destRowCount + 1)) {
    var isLastPage = true;

        var __destColIndex = pyjslib_range(destColCount).__iter__();
        try {
            while (true) {
                var destColIndex = __destColIndex.next();
                
        
    grid.clearCell(destRowIndex, destColIndex);

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }
        
    destRowIndex += 1;
    }
    navbar.gotoNet.setEnabled(!(isLstPage));
    navbar.gotoFirst.setEnabled((startRow > 0));
    navbar.gotoPrev.setEnabled((startRow > 0));
    setStatusText(startRow + 1 + " - " + startRow + srcRowCount);
};
