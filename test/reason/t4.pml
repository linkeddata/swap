
<!-- Processed by Id: cwm.py,v 1.176 2005/08/10 17:03:22 syosi Exp -->
<!--     using base file:/devel/WWW/2000/10/swap/test/reason/t4.proof-->


<rdf:RDF xmlns="http://inferenceweb.stanford.edu/2004/07/iw.owl#"
    xmlns:iw="http://inferenceweb.stanford.edu/2004/07/iw.owl#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">

    <DirectAssertion rdf:nodeID="b1">
        <source rdf:resource="t4.n3"/>
    </DirectAssertion>

    <rdf:Description>
        <rdf:type rdf:resource="http://inferenceweb.stanford.edu/2004/07/iw.owl#NodeSet"/>
        <conclusion>     @prefix : &#60;file:/devel/WWW/2000/10/swap/test/reason/t4.n3#&#62; .
     @prefix log: &#60;http://www.w3.org/2000/10/swap/log#&#62; .
    
     @forAll :x .
    
    :a     :b :c .
    
    :c     :d :e .
    {
        :a     :b :x .
        
        }     log:implies {:x     :d :e .
        } .
    
</conclusion>
        <hasInferenceEngine rdf:resource="http://inferenceweb.stanford.edu/registry/IE/CWM.owl#CWM"/>
        <hasLanguage rdf:resource="http://www.w3.org/2004/06/rei#N3"/>
    </rdf:Description>

    <rdf:Description>
        <conclusion>     @prefix : &#60;file:/devel/WWW/2000/10/swap/test/reason/t4.n3#&#62; .
    
    :a     :b :c .
    
</conclusion>
    </rdf:Description>

    <rdf:Description>
        <conclusion>     @prefix : &#60;file:/devel/WWW/2000/10/swap/test/reason/t4.n3#&#62; .
     @prefix log: &#60;http://www.w3.org/2000/10/swap/log#&#62; .
    
     @forAll :x .
    {
        :a     :b :x .
        
        }     log:implies {:x     :d :e .
        } .
    
</conclusion>
    </rdf:Description>

    <rdf:Description>
        <conclusion>     @prefix : &#60;file:/devel/WWW/2000/10/swap/test/reason/t4.n3#&#62; .
    
    :c     :d :e .
    
</conclusion>
    </rdf:Description>

    <rdf:Description>
        <rdf:type rdf:resource="http://inferenceweb.stanford.edu/2004/07/iw.owl#InferenceStep"/>
        <hasAntecedent rdf:parseType="Resource">
            <rdf:first rdf:parseType="Resource">
                <conclusion>     @prefix : &#60;file:/devel/WWW/2000/10/swap/test/reason/t4.n3#&#62; .
    
    :a     :b :c .
    
</conclusion>
            </rdf:first>
            <rdf:rest rdf:resource="http://www.w3.org/1999/02/22-rdf-syntax-ns#nil"/>
        </hasAntecedent>
        <hasRule rdf:parseType="Resource">
            <conclusion>     @prefix : &#60;file:/devel/WWW/2000/10/swap/test/reason/t4.n3#&#62; .
     @prefix log: &#60;http://www.w3.org/2000/10/swap/log#&#62; .
    
     @forAll :x .
    {
        :a     :b :x .
        
        }     log:implies {:x     :d :e .
        } .
    
</conclusion>
        </hasRule>
        <hasVariableMapping rdf:parseType="Resource">
            <term>file:/devel/WWW/2000/10/swap/test/reason/t4.n3#c</term>
            <variable>file:/devel/WWW/2000/10/swap/test/reason/t4.n3#x</variable>
        </hasVariableMapping>
    </rdf:Description>
</rdf:RDF>
