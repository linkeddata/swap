function greet(sender) {
    Windows_alert("Hello AJAX!");
}


function Hello() {
    return new __Hello();
}
function __Hello() {
}
__Hello.prototype.onModuleLoad = function() {
    var b = ui_Button("Click me", greet);
    ui_RootPanel().add(b);
};
