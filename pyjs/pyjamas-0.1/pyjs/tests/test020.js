__DayCheckBox.prototype = new __ui_CheckBox;
function DayCheckBox(caption, day) {
    return new __DayCheckBox(caption, day);
}
function __DayCheckBox(caption, day) {
    __ui_CheckBox.call(this, caption);
    this.day = day;
}
