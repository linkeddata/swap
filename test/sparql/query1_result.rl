<?xml version="1.0"?>


<sparql xmlns="http://www.w3.org/2005/06/sparqlResults#">

    <head>
        <variable http://www.w3.org/2005/06/sparqlResults#name="age"/>
        <variable http://www.w3.org/2005/06/sparqlResults#name="blurb"/>
        <variable http://www.w3.org/2005/06/sparqlResults#name="friend"/>
        <variable http://www.w3.org/2005/06/sparqlResults#name="hpage"/>
        <variable http://www.w3.org/2005/06/sparqlResults#name="mbox"/>
        <variable http://www.w3.org/2005/06/sparqlResults#name="name"/>
        <variable http://www.w3.org/2005/06/sparqlResults#name="x"/>
    </head>

    <results>
        <result>
            <binding http://www.w3.org/2005/06/sparqlResults#name="age">
                <literal http://www.w3.org/2005/06/sparqlResults#datatype="http://www.w3.org/2001/XMLSchema#integer">30</literal>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="blurb">
                <unbound/>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="friend">
                <bnode>http://example.com/swap/test/run#_g53</bnode>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="hpage">
                <uri>http://work.example.org/bob/</uri>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="mbox">
                <uri>mailto:bob@work.example.org</uri>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="name">
                <literal http://www.w3.org/XML/1998/namespace#lang="en">Bob</literal>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="x">
                <bnode>http://example.com/swap/test/run#_g54</bnode>
            </binding>
        </result>
        <result>
            <binding http://www.w3.org/2005/06/sparqlResults#name="age">
                <unbound/>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="blurb">
                <literal http://www.w3.org/2005/06/sparqlResults#datatype="http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral">&#60;p xmlns="http://www.w3.org/1999/xhtml"&#62;My name is &#60;em&#62;Alice&#60;/em&#62;&#60;/p&#62;</literal>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="friend">
                <bnode>http://example.com/swap/test/run#_g54</bnode>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="hpage">
                <uri>http://work.example.org/alice/</uri>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="mbox">
                <literal></literal>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="name">
                <literal http://www.w3.org/XML/1998/namespace#lang="he-il">Alice</literal>
            </binding>
            <binding http://www.w3.org/2005/06/sparqlResults#name="x">
                <bnode>http://example.com/swap/test/run#_g53</bnode>
            </binding>
        </result>
    </results>
</sparql>
