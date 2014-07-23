function ui_UIObject() {
    return new __ui_UIObject();
}
function __ui_UIObject() {
}
__ui_UIObject.prototype.setElement = function(element) {
    this.element = element;
};
__ui_Widget.prototype = new __ui_UIObject;
function ui_Widget() {
    return new __ui_Widget();
}
function __ui_Widget() {
}
__ui_FocusWidget.prototype = new __ui_Widget;
function ui_FocusWidget(element) {
    return new __ui_FocusWidget(element);
}
function __ui_FocusWidget(element) {
    this.setElement(element);
}
