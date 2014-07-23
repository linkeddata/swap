function test() {
    if (bar.__contains__(foo)) {
    do_something();
    }
    if (!bar.__contains__(foo)) {
    do_something_else();
    }
    if (foo || bar) {
    good();
    }
    if (foo && bar) {
    bad();
    }
}


