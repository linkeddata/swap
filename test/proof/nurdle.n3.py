#  Here is an example of a proof
#

@prefix p: <http://www.w3.org/2001/07/imaginary-proof-ontology>.

<> a p:Proof; p:of :step13; p:given ( <doc1> ).

:setp13
    p:subsitite  <#mary>;
    p:for    <v#q>;
    p:in  :step13; .

:step12    
    p:read { <joe> :loves <v#q>. this log:forAll <v#q> };
    p:from  [ = <doc1>; a p:trustedDocument].

# The following applies a rule to a set of informtion
# which has already had the substitution done.
             
:step10
    p:appliesRule  <#step9>.
    p:given ( :step9 :step8 :step7 ).

:step9 
    p:subsitite  <#alan>;
    p:for    <v#x>;
    p:in  [
        p:subsitite  <#bert>;
        p:for    <v#y>;
        p:in  :step7; ].


#ends
             
