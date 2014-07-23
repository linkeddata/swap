def i(x):
    return x

def test_builtins():
    x = []
    y = callable(x)
    z = map(i, x)
    filter(callable, z)
    dir(x)
    if hasattr(x, "foo"):
        foo = getattr(x, "foo")

test_builtins()