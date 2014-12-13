<?xml version="1.0"?>
<!-- $Id$-->

<xsl:transform
  xmlns:xsl  ="http://www.w3.org/1999/XSL/Transform"  version="1.0"
  xmlns:rdf  ="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:p3p  ="http://www.w3.org/2002/01/P3Pv1"
  xmlns:p3pr ="http://www.w3.org/2002/01/P3Pv1"
  xmlns:p3dr ="http://www.w3.org/TR/P3P/base#"
  xmlns:ont  ="http://www.daml.org/2001/03/daml+oil#"
  >

<xsl:output method="xml" indent="yes"/>

<!-- The structure of this code roughly follows the XML Schema for P3P
http://www.w3.org/TR/2001/WD-P3P-20010928/#Appendix_schema
except that attributes go before elements -->


<xsl:variable name="P3P_pfx" select='"http://www.w3.org/2001/09/P3Pv1#"'/>
<xsl:variable name="DataPfx" select='"http://www.w3.org/TR/P3P/base#"'/>

<xsl:variable name="InfoClassPfx" select='"http://www.w3.org/2001/09/P3Pv1#InfoClass-"'/> <!-- @@this should come from a bwm namespace, not the P3P namespace, no? -->
<xsl:variable name="RecipientPfx" select='"http://www.w3.org/2001/09/P3Pv1#Recipient-"'/>
<xsl:variable name="RetentionPfx" select='"http://www.w3.org/2001/09/P3Pv1#Retention-"'/>
<xsl:variable name="PurposePfx" select='"http://www.w3.org/2001/09/P3Pv1#Purpose-"'/>

<div xmlns="http://www.w3.org/1999/xhtml">
<p>working toward example rules in the APPEL spec;
input data: forShoppers policy</p>
</div>

<xsl:variable name='Category_NS' select='"@@where-do-p3p-categories-live-in-URI-space#"'/>

<xsl:template match="p3p:POLICIES">
  <rdf:RDF>
    <xsl:if test="p3p:EXPIRY">
      <rdf:Description rdf:about="">
        <p3pr:expiry p3p:max-age="{p3p:EXPIRY/@max-age}"/>
      </rdf:Description>
    </xsl:if>

    <xsl:if test="p3p:DATASCHEMA">
      <xsl:message>@@don't grok DATASCHEMA yet</xsl:message>
    </xsl:if>

    <xsl:for-each select="p3p:POLICY">
    <p3pr:Policy rdf:about='{concat("#", @name)}'> <!-- absolutize? -->

      <!-- factor out common template? -->
      <xsl:if test='@discuri'>
        <p3pr:discuri rdf:resource='{@discuri}'/>
      </xsl:if>
      <xsl:if test='@opturi'>
        <p3pr:opturi rdf:resource='{@opturi}'/>
      </xsl:if>

      <xsl:if test='p3p:EXTENSION'>
        <xsl:message terminate="yes">@@don't grok EXTENSION yet</xsl:message>
      </xsl:if>

      <xsl:if test='p3p:TEST'>
        <xsl:message>@@NOTE: this is only a test policy</xsl:message>
      </xsl:if>

      <xsl:for-each select='p3p:ENTITY'>
	<p3pr:entity rdf:parseType="Resource">
  	  <xsl:call-template name="immediateData"/>
        </p3pr:entity>

        <xsl:if test='p3p:EXTENSION'>
          <xsl:message terminate="yes">@@don't grok EXTENSION yet</xsl:message>
        </xsl:if>
      </xsl:for-each>

      <!-- @@"and that's all" property to the list of disputes? -->
      <xsl:call-template name="eachPO">
        <xsl:with-param name="elt" select='"ACCESS"'/>
        <xsl:with-param name="propName" select='"access"'/>
        <xsl:with-param name="prefix" select='$InfoClassPfx'/>
      </xsl:call-template>

      <!-- @@"and that's all" property to the list of disputes? -->
      <xsl:for-each select='p3p:DISPUTES-GROUP/p3p:DISPUTES'>
        <xsl:call-template name="grokDisputes"/>
      </xsl:for-each>

      <xsl:for-each select='p3p:STATEMENT'>
        <xsl:call-template name="grokStatement"/>
      </xsl:for-each>

    </p3pr:Policy>
    </xsl:for-each>

  </rdf:RDF>

</xsl:template>

<xsl:template name="immediateData">
  <!-- interpret <DATA-GROUP> as immediate data, not as a template -->
  <!-- hm... should perhaps complain if we see DATA/CATEGORIES
	or DATA/@optional
    -->

  <xsl:variable name='propNS'>
    <xsl:choose>
      <xsl:when test='p3p:DATA-GROUP/@base'>
        <xsl:value-of select='p3p:DATA-GROUP/@base'/>
      </xsl:when>

      <xsl:otherwise>
	<xsl:value-of select='$DataPfx'/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:for-each select='p3p:DATA-GROUP/p3p:DATA'>
    <xsl:variable name='ref' select='@ref'/>

    <xsl:if test='not(starts-with($ref, "#"))'>
      <xsl:message terminate="yes">@@don't yet grok ref attributes that don't start with #</xsl:message>
    </xsl:if>

    <xsl:element name="{substring($ref, 2)}" namespace="{$propNS}">
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:for-each>
</xsl:template>



<xsl:template name="templateData">
  <!-- interpret <DATA-GROUP> as a template -->

  <xsl:variable name='propNS'>
    <xsl:choose>
      <xsl:when test='p3p:DATA-GROUP/@base'>
        <xsl:value-of select='p3p:DATA-GROUP/@base'/>
      </xsl:when>

      <xsl:otherwise>
	<xsl:value-of select='$DataPfx'/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:for-each select='p3p:DATA-GROUP/p3p:DATA'>
    <xsl:variable name='ref' select='@ref'/>

    <xsl:if test='not(starts-with($ref, "#"))'>
      <xsl:message terminate="yes">@@don't yet grok ref attributes that don't start with #</xsl:message>
    </xsl:if>

    <xsl:variable name="prop" select='concat($propNS, substring($ref, 2))'/>

    <p3pr:data rdf:parseType="Resource">
      <p3pr:ref rdf:resource="{$prop}"/>
      <xsl:for-each select="p3p:CATEGORIES/*">
        <p3pr:categories rdf:resource="{concat(namespace-uri(), '#', local-name())}"/>
      </xsl:for-each>

      <xsl:if test="@optional">
        <p3pr:optional><xsl:value-of select="@optional"/></p3pr:optional>
      </xsl:if>
    </p3pr:data>
  </xsl:for-each>
</xsl:template>





<xsl:template name="eachPO">
  <xsl:param name="elt"/>
  <xsl:param name="propName"/>
  <xsl:param name="prefix"/>

  <!-- @@should support EXTENSION -->

  <xsl:for-each select='*[(concat(namespace-uri(), "#") = $P3P_pfx) and (local-name() = $elt)]/*'>
    <xsl:variable name="n" select='name()'/>

    <xsl:element name='{$propName}' namespace='{$P3P_pfx}'>
      <xsl:attribute name="rdf:resource"><xsl:value-of select='concat($prefix, $n)'/></xsl:attribute>
    </xsl:element>
  </xsl:for-each>
</xsl:template>


<xsl:template name="grokDisputes">
        <p3pr:disputes rdf:parseType="Resource">

	<p3pr:resolution-type><xsl:value-of select='@resolution-type'/></p3pr:resolution-type>
	<p3pr:service rdf:resource="{@service}"/>
	<xsl:if test="@verification">
          <p3pr:verification><xsl:value-of select="@verification"/></p3pr:verification>
        </xsl:if>
	<xsl:if test="@short-description">
          <p3pr:short-description><xsl:value-of select="@short-description"/></p3pr:short-description>
        </xsl:if>

        <!-- factor out this pattern? -->
        <!-- might look better as an attribute... -->
        <xsl:if test='p3p:LONG-DESCRIPTION'>
          <p3pr:long-description><xsl:value-of select='p3p:LONG-DESCRIPTION'/></p3pr:long-description>
        </xsl:if>

	 <!-- at most one allowed, but for-each sets the context
		node in a very convenient way. -->
        <xsl:for-each select='p3p:IMG'>
          <p3pr:img>
            <rdf:Description rdf:about="{@src}">
              <p3pr:alt><xsl:value-of select="@alt"/></p3pr:alt>
              <xsl:if test="@width">
                <p3pr:width><xsl:value-of select="@width"/></p3pr:width>
              </xsl:if>
              <xsl:if test="@height">
                <p3pr:width><xsl:value-of select="@height"/></p3pr:width>
              </xsl:if>
            </rdf:Description>
          </p3pr:img>
        </xsl:for-each>

        <!-- @@use a sequence to hint at "and that's all" even
		though RDF sequences are broken in this way?
                nah... let's use DAML+OIL collections,
		if only to force the issue... -->
        <p3pr:remedies rdf:parseType="ont:collection">
          <xsl:for-each select='p3p:REMEDIES/*'>
	  <!-- @@hmm... concat? -->
            <rdf:Description rdf:about="{concat(namespace-uri(), '#', local-name())}"/>
          </xsl:for-each>
        </p3pr:remedies>

	<xsl:if test='p3p:EXTENSION'>
	  <xsl:message terminate="yes">@@don't grok EXTENSION yet</xsl:message>
        </xsl:if>


        </p3pr:disputes>

</xsl:template>

<xsl:template name="grokStatement">
	<p3pr:statement rdf:parseType="Resource">
	  <xsl:for-each select='p3p:CONSEQUENCE'> <!-- just one -->
	    <p3pr:consequence><xsl:value-of select='.'/></p3pr:consequence>
	  </xsl:for-each>

	  <xsl:if test="p3p:NON-IDENTIFIABLE">
            <p3pr:non-identifiable>1</p3pr:non-identifiable> <!-- @@use a class? -->
          </xsl:if>


      <xsl:call-template name="eachPO">
        <xsl:with-param name="elt" select='"PURPOSE"'/>
        <xsl:with-param name="propName" select='"purpose"'/>
        <xsl:with-param name="prefix" select='$PurposePfx'/>
      </xsl:call-template>
      <xsl:message>@@recipient: there may be more to it than this...</xsl:message>
      <xsl:call-template name="eachPO">
        <xsl:with-param name="elt" select='"RECIPIENT"'/>
        <xsl:with-param name="propName" select='"recipient"'/>
        <xsl:with-param name="prefix" select='$RecipientPfx'/>
      </xsl:call-template>
      <xsl:call-template name="eachPO">
        <xsl:with-param name="elt" select='"RETENTION"'/>
        <xsl:with-param name="propName" select='"retention"'/>
        <xsl:with-param name="prefix" select='$RetentionPfx'/>
      </xsl:call-template>

	<xsl:call-template name="templateData"/>

	<xsl:if test='p3p:EXTENSION'>
	  <xsl:message terminate="yes">@@don't grok EXTENSION yet</xsl:message>
        </xsl:if>
    </p3pr:statement>
</xsl:template>

<!-- don't pass text thru -->
<xsl:template match="text()|@*">
</xsl:template>

</xsl:transform>
