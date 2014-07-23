function Foo() {
    return new __Foo();
}
function __Foo() {
}
__Foo.BAR = __Foo.prototype.BAR = 1;
__Foo.BAZ = __Foo.prototype.BAZ = 2;
function test() {
    return __Foo.BAR;
}


