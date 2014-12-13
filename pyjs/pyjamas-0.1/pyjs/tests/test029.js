function DynaTableWidget() {
    return new __DynaTableWidget();
}
function __DynaTableWidget() {
}
__DynaTableWidget.prototype.initTable = function(columns, columnStyles, rowCount) {
    this.grid.resize(rowCount + 1, pyjslib_len(columns));

        var __i = pyjslib_range(pyjslib_len(columns)).__iter__();
        try {
            while (true) {
                var i = __i.next();
                
        
    var caption = columns.__getitem__(i);
    this.grid.setText(0, i, columns.__getitem__(i));

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }
        
};
