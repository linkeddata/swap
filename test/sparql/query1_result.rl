<?xml version="1.0"?>


<sparql xmlns="http://www.w3.org/2005/sparql-results#">

    <head>
        <variable name="friend"/>
        <variable name="blurb"/>
        <variable name="age"/>
        <variable name="mbox"/>
        <variable name="name"/>
        <variable name="hpage"/>
        <variable name="x"/>
    </head>

    <results>
        <result>
            <binding name="friend">
                <bnode>http://example.com/swap/test/run#_g131</bnode>
            </binding>
            <binding name="blurb">
                <literal datatype="http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral">&#60;p xmlns="http://www.w3.org/1999/xhtml"&#62;My name is &#60;em&#62;Alice&#60;/em&#62;&#60;/p&#62;</literal>
            </binding>
            <binding name="mbox">
                <literal></literal>
            </binding>
            <binding name="name">
                <literal>Alice</literal>
            </binding>
            <binding name="hpage">
                <uri>http://work.example.org/alice/</uri>
            </binding>
            <binding name="x">
                <bnode>http://example.com/swap/test/run#_g130</bnode>
            </binding>
        </result>
        <result>
            <binding name="friend">
                <bnode>http://example.com/swap/test/run#_g122</bnode>
            </binding>
            <binding name="age">
                <literal datatype="http://www.w3.org/2001/XMLSchema#integer">30</literal>
            </binding>
            <binding name="mbox">
                <uri>mailto:bob@work.example.org</uri>
            </binding>
            <binding name="name">
                <literal xml:lang="en">Bob</literal>
            </binding>
            <binding name="hpage">
                <uri>http://work.example.org/bob/</uri>
            </binding>
            <binding name="x">
                <bnode>http://example.com/swap/test/run#_g123</bnode>
            </binding>
        </result>
    </results>
</sparql>
