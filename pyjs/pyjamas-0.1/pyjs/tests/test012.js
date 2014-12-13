function Widget() {
    return new __Widget();
}
function __Widget() {
    this.attached = false;
}
__Widget.prototype.setParent = function(parent) {
    this.parent = parent;
    if ((parent == null)) {
    this.onDetach();
    }
    else if (parent.attached) {
    this.onAttach();
    }
};
__Widget.prototype.onAttach = function() {
    if (this.attached) {
    return;
    }
    this.attached = true;
    DOM_setEventListener(this.getElement(), this);
};
__Widget.prototype.onDetach = function() {
    if (!(this.attached)) {
    return;
    }
    this.attached = false;
    DOM_setEventListener(this.getElement(), null);
};
