function Test() {
    return new __Test();
}
function __Test() {
}
__Test.prototype.test = function(foo) {
    if (typeof foo == 'undefined') foo=5;
};
