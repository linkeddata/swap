# test proof API
from swap import myStore, diag, why
from swap.myStore import formula, symbol

diag.tracking = 1
f = formula()
rea = why.Premise("because I said so")
pred = symbol("http://example.com/weather")
f.add("Boston", pred, "sunny", why=rea)
f.add("Chicago", pred, "snowy", why=rea)

rea = why.Premise("because CNN said so")
f.add("Fort Myers", pred, "stormy", why=rea)

f = f.close()
g = why.explainFormula(f)
print g.n3String()

