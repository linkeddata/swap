1i\
@prefix qu:  <http://www.w3.org/2000/10/swap/pim/qif#>.

# Convert check payee hand-entered information to n3
s/^\([0-9]*\) \(.*\)/"\1"  qu:checkWrittenTo "\2"./
#ends
