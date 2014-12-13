function TimeSlot() {
    return new __TimeSlot();
}
function __TimeSlot() {
}
__TimeSlot.prototype.getDescription = function() {
    return this.getHrsMins(this.startMinutes) + "-" + this.getHrsMins(this.endMinutes);
};
