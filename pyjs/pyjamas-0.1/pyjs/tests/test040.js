function Foo() {
    return new __Foo();
}
function __Foo() {
}
__Foo.mu = __Foo.prototype.mu = 5;
__Foo.prototype.test = function() {
    var foo = 5;
    baz.__setitem__(1, 5);
    bar.foo = 5;
    this.foo = 5;
    biz.baz.foo = 5;
    baz.__getitem__(2).foo = 5;
    foo += 5;
    bar.foo += 5;
};
