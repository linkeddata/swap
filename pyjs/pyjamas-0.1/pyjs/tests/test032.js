function i(x) {
    return x;
}


function test_builtins() {
    var x = new pyjslib_List([]);
    var y = pyjslib_isFunction(x);
    var z = pyjslib_map(i, x);
    pyjslib_filter(callable, z);
    pyjslib_dir(x);
    if (pyjslib_hasattr(x, "foo")) {
    var foo = pyjslib_getattr(x, "foo");
    }
}


    test_builtins();
