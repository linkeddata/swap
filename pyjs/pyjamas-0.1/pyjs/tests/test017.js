function TimeSlot() {
    return new __TimeSlot();
}
function __TimeSlot() {
}
__TimeSlot.DAYS = __TimeSlot.prototype.DAYS = new pyjslib_List(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]);
__TimeSlot.prototype.getDescription = function() {
    return this.DAYS.__getitem__(this.dayOfWeek) + " " + this.getHrsMins(this.startMinutes) + "-" + this.getHrsMins(this.endMinutes);
};
__TimeSlot.prototype.getHrsMins = function(mins) {
};
