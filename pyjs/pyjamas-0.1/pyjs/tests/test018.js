function getHrsMins(mins) {
    var hrs = mins / 60;
    if ((hrs > 12)) {
    hrs -= 12;
    }
    var remainder = mins % 60;
    if ((remainder < 10)) {
    var string_mins = "0" + pyjslib_str(remainder);
    }
    else {
    var string_mins = pyjslib_str(remainder);
    }
    return pyjslib_str(hrs) + ":" + string_mins;
}


