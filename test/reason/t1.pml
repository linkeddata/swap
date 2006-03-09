
<!-- Processed by Id: cwm.py,v 1.183 2006/01/13 14:48:54 syosi Exp -->
<!--     using base file:/home/connolly/w3ccvs/WWW/2000/10/swap/test/reason/-->


<rdf:RDF xmlns="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:iw="http://inferenceweb.stanford.edu/2004/07/iw.owl#"
    xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:rea="http://www.w3.org/2000/10/swap/reason#"
    xmlns:s="http://www.w3.org/2000/01/rdf-schema#">

    <iw:NodeSet rdf:about="#aux__g47">
        <iw:hasConclusion>    
    &#60;file:/home/connolly/w3ccvs/WWW/2000/10/swap/test/reason/a&#62;     &#60;file:/home/connolly/w3ccvs/WWW/2000/10/swap/test/reason/b&#62; &#60;file:/home/connolly/w3ccvs/WWW/2000/10/swap/test/reason/c&#62; .
    
</iw:hasConclusion>
        <iw:hasLanguage rdf:resource="http://www.w3.org/2004/06/rei#N3"/>
        <iw:isConsequentOf rdf:parseType="Resource">
            <rdf:type rdf:resource="http://inferenceweb.stanford.edu/2004/07/iw.owl#InferenceStep"/>
            <rdf:type rdf:resource="http://www.w3.org/2000/10/swap/reason#Parsing"/>
            <rdf:type rdf:resource="http://www.w3.org/2000/10/swap/reason#Proof"/>
            <rdf:type rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
            <aux xmlns="file:/home/connolly/w3ccvs/WWW/2000/10/swap/test/reason/to-pml.n3#"
                rdf:parseType="Resource">
            </aux>
            <iw:hasInferenceEngine rdf:resource="http://inferenceweb.stanford.edu/registry/IE/CWM.owl#CWM"/>
            <iw:hasRule rdf:resource="http://inferenceweb.stanford.edu/registry/DPR/Told.owl#Told"/>
            <iw:hasSourceUsage rdf:parseType="Resource">
                <rdf:type rdf:resource="http://inferenceweb.stanford.edu/2004/07/iw.owl#SourceUsage"/>
                <iw:hasSource rdf:resource="t1.n3"/>
		<iw:usageTime rdf:datatype="http://www.w3.org/2001/XMLSchema#dateTime">2006-02-18T04:04:04Z</iw:usageTime>
            </iw:hasSourceUsage>
            <rea:source rdf:resource="t1.n3"/>
        </iw:isConsequentOf>
        <label>@@step</label>
    </iw:NodeSet>

    <Class rdf:about="http://www.w3.org/2000/10/swap/reason#Binding">
        <comment>A binding is given eg in a proof or query result

	</comment>
        <label>binding</label>
    </Class>

    <rdf:Description rdf:about="http://www.w3.org/2000/10/swap/reason#CommandLine">
        <subClassOf rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
    </rdf:Description>

    <rdf:Description rdf:about="http://www.w3.org/2000/10/swap/reason#Conjunction">
        <label>The step of conjunction introduction: 
	taking a bunch of compent statements
	and building a formula from them.</label>
        <subClassOf rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
    </rdf:Description>

    <rdf:Description rdf:about="http://www.w3.org/2000/10/swap/reason#Extraction">
        <comment>The step of taking one statement out of a formula.
	The step is identified by the :gives formula (the statement)
	and the :because step's :gives formula (the formula extracted
	from).
	</comment>
        <label>Conjunction elimination</label>
        <subClassOf rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
    </rdf:Description>

    <rdf:Description rdf:about="http://www.w3.org/2000/10/swap/reason#Inference">
        <subClassOf rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
    </rdf:Description>

    <rdf:Description rdf:about="http://www.w3.org/2000/10/swap/reason#Parsing">
        <comment>The formula given was derived from parsing a
	resource.</comment>
        <label>parsing</label>
        <subClassOf rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
    </rdf:Description>

    <rdf:Description rdf:about="http://www.w3.org/2000/10/swap/reason#Proof">
        <comment>A Proof step is the last step in the proof, 
	a step which :gives that which was to be proved.
	Typically a document will assert just one :Proof,
	which a checker can then check and turn into
	the Formula proved - Q.E.D. .
	</comment>
        <label>proof</label>
        <subClassOf rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
    </rdf:Description>

    <Class rdf:about="http://www.w3.org/2000/10/swap/reason#Step">
        <comment>A step in a proof.

	See :gives for the arc to the formula proved at this step.
	</comment>
        <label>proof step</label>
    </Class>

    <rdf:Property rdf:about="http://www.w3.org/2000/10/swap/reason#because">
        <comment>gives the step whose data was input to this step.</comment>
        <domain rdf:resource="http://www.w3.org/2000/10/swap/reason#Extraction"/>
        <label>because</label>
        <range rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
    </rdf:Property>

    <rdf:Property rdf:about="http://www.w3.org/2000/10/swap/reason#boundTo">
        <comment>
	This binding binds its variable to this term.
	</comment>
        <domain rdf:resource="http://www.w3.org/2000/10/swap/reason#Binding"/>
        <label>bound to</label>
        <range rdf:resource="http://www.w3.org/2000/10/swap/reify#Term"/>
    </rdf:Property>

    <rdf:Property rdf:about="http://www.w3.org/2000/10/swap/reason#component">
        <comment>A step whose data was used in building this conjunction</comment>
        <domain rdf:resource="http://www.w3.org/2000/10/swap/reason#Conjunction"/>
        <label>component</label>
        <range rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
    </rdf:Property>

    <rdf:Property rdf:about="http://www.w3.org/2000/10/swap/reason#gives">
        <domain rdf:resource="http://www.w3.org/2000/10/swap/reason#Step"/>
        <label>gives</label>
        <range rdf:resource="http://www.w3.org/2000/10/swap/reify#Formula"/>
    </rdf:Property>

    <rdf:Property rdf:about="http://www.w3.org/2000/10/swap/reason#source">
        <comment>The source document which was parsed.
	</comment>
        <domain rdf:resource="http://www.w3.org/2000/10/swap/reason#Parsing"/>
        <label>source</label>
        <range rdf:resource="http://www.w3.org/2000/10/swap/pim/soc#Work"/>
    </rdf:Property>

    <rdf:Property rdf:about="http://www.w3.org/2000/10/swap/reason#variable">
        <comment>
	The given string is that used as the identifier of the variable
	which is bound by this binding.  The variable name has to be given as
	a string, rather than the variable being put here, or the variable
	would be treated as a variable.</comment>
        <domain rdf:resource="http://www.w3.org/2000/10/swap/reason#Binding"/>
        <label>variable</label>
        <range rdf:resource="http://www.w3.org/2000/10/swap/reify#String"/>
    </rdf:Property>
</rdf:RDF>
