function CalendarProvider() {
    return new __CalendarProvider();
}
function __CalendarProvider() {
}
__CalendarProvider.prototype.pushResults = function(acceptor, startRow, people) {
    var rows = new pyjslib_List([]);

        var __person = people.__iter__();
        try {
            while (true) {
                var person = __person.next();
                
        
    rows.append(new pyjslib_Tuple([person.getName(), person.getDescription(), person.getSchedule(daysFilter)]));

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }
        
    acceptor.accept(startRow, rows);
};
