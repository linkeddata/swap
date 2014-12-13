function SchoolCalendarWidget() {
    return new __SchoolCalendarWidget();
}
function __SchoolCalendarWidget() {
}
__SchoolCalendarWidget.prototype.setDayIncluded = function(day, included) {
    if ((this.daysFilter.__getitem__(day) == included)) {
    return;
    }
    this.daysFilter.__setitem__(day, included);
};
