function Hello() {
    return new __Hello();
}
function __Hello() {
}
__Hello.prototype.onModuleLoad = function() {
    var b = ui_Button("Click me");
    ui_RootPanel().add(b);
};
