function ui_UIObject() {
    return new __ui_UIObject();
}
function __ui_UIObject() {
}
__ui_UIObject.prototype.getElement = function() {
    return this.element;
};
__ui_UIObject.prototype.setElement = function(element) {
    this.element = element;
};
__ui_UIObject.prototype.setStyleName = function(style) {
    DOM_setAttribute(this.element, "className", style);
};
__ui_Widget.prototype = new __ui_UIObject;
function ui_Widget() {
    return new __ui_Widget();
}
function __ui_Widget() {
}
__ui_Widget.prototype.setParent = function(parent) {
    this.parent = parent;
};
__ui_Panel.prototype = new __ui_Widget;
function ui_Panel() {
    return new __ui_Panel();
}
function __ui_Panel() {
}
__ui_ComplexPanel.prototype = new __ui_Panel;
function ui_ComplexPanel() {
    return new __ui_ComplexPanel();
}
function __ui_ComplexPanel() {
    this.children = new pyjslib_List([]);
}
__ui_ComplexPanel.prototype.add = function(widget) {
    this.children.append(widget);
    widget.setParent(this);
    return true;
};
