function ui_UIObject() {
    return new __ui_UIObject();
}
function __ui_UIObject() {
}
__ui_Widget.prototype = new __ui_UIObject;
function ui_Widget() {
    return new __ui_Widget();
}
function __ui_Widget() {
}
__ui_Widget.prototype.setParent = function(parent) {
    this.parent = parent;
};
