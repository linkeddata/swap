#  Extract list of constants from axioms.n3
#
s/[ \t]*<\(#[A-Za-z_]*\)>.*/  <axioms.n3\1> a ko:Constant .  # Constant in axioms/g
/Constant in axioms/!d
