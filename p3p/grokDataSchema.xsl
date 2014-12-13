<?xml version="1.0"?>
<!-- $Id$-->
<xsl:transform
  xmlns:xsl  ="http://www.w3.org/1999/XSL/Transform"  version="1.0"
  xmlns:rdf  ="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:p3p  ="http://www.w3.org/2001/09/P3Pv1"
  xmlns:p3pr ="http://www.w3.org/2001/09/P3Pv1#"
  >

<xsl:output method="xml" indent="yes"/>

<div xmlns="http://www.w3.org/1999/xhtml">
<p>working toward example rules in the APPEL spec;
need base data schema in RDF; hence this hack</p>
</div>

<xsl:param name="Base" select='"http://www.w3.org/TR/P3P/base"'/>

<xsl:template match="p3p:DATASCHEMA">
  <rdf:RDF>
    <!-- interpret p3p:DATASCHEMA as a class of documents -->
    <p3pr:DataSchema rdf:about=""/>

    <xsl:for-each select='p3p:DATA-STRUCT'>
      <p3pr:Data-Struct rdf:about='{concat($Base, "#", @name)}'>
        <xsl:if test='@short-description'>
	  <!-- might look nicer using a propAttr... -->
	  <p3pr:short-description><xsl:value-of select='@short-description'/></p3pr:short-description>
	</xsl:if>

	<!-- losing information about end of list? @@ -->
        <xsl:for-each select='p3p:CATEGORIES/*'>
	  <!-- @@hmm... concat? -->
	  <p3pr:categories rdf:resource="{concat(namespace-uri(), '#', local-name())}"/>
	</xsl:for-each>

	<!-- @@ more... -->
      </p3pr:Data-Struct>
    </xsl:for-each>

    <xsl:for-each select='p3p:DATA-DEF'>
      <p3pr:Data-Def rdf:about='{concat($Base, "#", @name)}'>
        <xsl:if test='@short-description'>
	  <!-- might look nicer using a propAttr... -->
	  <p3pr:short-description><xsl:value-of select='@short-description'/></p3pr:short-description>
	</xsl:if>

        <xsl:if test='@structref'>
          <!-- @@ combine structref with $Base per RFC2396 -->
	  <p3pr:structref rdf:resource="{concat($Base, @structref)}"/>
	</xsl:if>

	<!-- losing information about end of list? @@ -->
        <xsl:for-each select='p3p:CATEGORIES/*'>
	  <!-- @@hmm... concat? -->
	  <p3pr:categories rdf:resource="{concat(namespace-uri(), '#', local-name())}"/>
	</xsl:for-each>

	<!-- @@ more... -->
      </p3pr:Data-Def>
    </xsl:for-each>

    <!-- @@ more... -->
  </rdf:RDF>
</xsl:template>

</xsl:transform>
