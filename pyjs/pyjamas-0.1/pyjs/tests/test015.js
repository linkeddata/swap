function TimeSlot(dayOfWeek, startMinutes, endMinutes) {
    return new __TimeSlot(dayOfWeek, startMinutes, endMinutes);
}
function __TimeSlot(dayOfWeek, startMinutes, endMinutes) {
    this.dayOfWeek = dayOfWeek;
    this.startMinutes = startMinutes;
    this.endMinutes = endMinutes;
}
__TimeSlot.prototype.compareTo = function(other) {
    if ((this.dayOfWeek < other.dayOfWeek)) {
    return -1;
    }
    else if ((this.dayOfWeek > other.dayOfWeek)) {
    return 1;
    }
    else {
    if ((this.startMinutes < other.startMinutes)) {
    return -1;
    }
    else if ((this.startMinutes > other.startMinutes)) {
    return 1;
    }
    }
    return 0;
};
