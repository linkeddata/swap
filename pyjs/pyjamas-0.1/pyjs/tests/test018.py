def getHrsMins(mins):
    hrs = mins / 60
    if hrs > 12:
        hrs -= 12
    remainder = mins % 60
    if remainder < 10:
        string_mins = "0" + str(remainder)
    else:
        string_mins = str(remainder)
    return str(hrs) + ":" + string_mins
