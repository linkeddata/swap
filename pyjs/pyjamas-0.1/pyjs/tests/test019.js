function Schedule() {
    return new __Schedule();
}
function __Schedule() {
    this.timeSlots = new pyjslib_List([]);
}
__Schedule.prototype.addTimeSlot = function(timeSlot) {
    this.timeSlots.append(timeSlot);
};
__Schedule.prototype.getDescription = function(daysFilter) {
    var s = null;

        var __timeSlot = this.timeSlots.__iter__();
        try {
            while (true) {
                var timeSlot = __timeSlot.next();
                
        
    if (daysFilter.__getitem__(timeSlot.dayOfWeek)) {
    if (!(s)) {
    var s = timeSlot.getDescription();
    }
    else {
    s += ", " + timeSlot.getDescription();
    }
    }

            }
        } catch (e) {
            if (e != StopIteration) {
                throw e;
            }
        }
        
    if (s) {
    return s;
    }
    else {
    return "";
    }
};
