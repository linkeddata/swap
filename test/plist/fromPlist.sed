/^<?xml/d
/^<!DOCTYPE/d
s/^<plist.*>/@prefix : <#>. @prefix plist: <whatever>./
/^<.plist>/d
s?<key></key>?plist:is?
s?<key>\(.*\)</key>? :\1?
s?<string>\(.*\)</string>?"\1";?
s?<array>?[plist:contains?
s?</array>?];?
s?<dict>?[?
s?</dict>?];?
$i\
.\
#ends
#ends
