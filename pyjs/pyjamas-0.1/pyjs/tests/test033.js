function test() {
    var a = y;
    var b = x.y;
    var c = this.y;
    var d = __foo_bar.y;
    var e = __Baz.y;
    var f = x.y.z;
    var g = x.__getitem__(0).y;
    var h = x().y;
}


