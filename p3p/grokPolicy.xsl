<?xml version="1.0"?>
<!-- $Id$-->

<xsl:transform
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"  version="1.0"
  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:p3p="http://www.w3.org/2001/09/P3Pv1"
  xmlns:p3pr="http://www.w3.org/2001/09/P3Pv1#"
  >

<xsl:output method="xml" indent="yes"/>

<xsl:variable name="P3P_pfx" select='"http://www.w3.org/2001/09/P3Pv1#"'/>
<xsl:variable name="DataPfx" select='"http://www.w3.org/TR/P3P/base"'/>

<xsl:variable name="InfoClassPfx" select='"http://www.w3.org/2001/09/P3Pv1#InfoClass-"'/> <!-- @@this should come from a bwm namespace, not the P3P namespace, no? -->
<xsl:variable name="RecipientPfx" select='"http://www.w3.org/2001/09/P3Pv1#Recipient-"'/>
<xsl:variable name="RetentionPfx" select='"http://www.w3.org/2001/09/P3Pv1#Retention-"'/>
<xsl:variable name="PurposePfx" select='"http://www.w3.org/2001/09/P3Pv1#Purpose-"'/>

<div xmlns="http://www.w3.org/1999/xhtml">
<p>working toward example rules in the APPEL spec;
input data: forShoppers policy</p>
</div>

<xsl:variable name='Category_NS' select='"@@where-do-p3p-categories-live-in-URI-space#"'/>

<xsl:template match="p3p:POLICY">
  <rdf:RDF>
    <p3pr:Policy rdf:about='{concat("#", @name)}'> <!-- absolutize? -->

      <!-- factor out common template? -->
      <xsl:if test='@discuri'>
        <p3pr:discuri rdf:resource='{@discuri}'/>
      </xsl:if>
      <xsl:if test='@opturi'>
        <p3pr:opturi rdf:resource='{@opturi}'/>
      </xsl:if>

      <xsl:for-each select='p3p:ENTITY'>
	<p3pr:entity rdf:parseType="Resource">

	  <!-- KLUDGE! @@ -->
	  <p3pr:business.name><xsl:value-of select='p3p:DATA-GROUP/p3p:DATA[@ref="#business.name"]'/></p3pr:business.name>

	  <!-- @@MORE... -->
        </p3pr:entity>
      </xsl:for-each>

      <xsl:call-template name="eachPO">
        <xsl:with-param name="elt" select='"ACCESS"'/>
        <xsl:with-param name="propName" select='"access"'/>
        <xsl:with-param name="prefix" select='$InfoClassPfx'/>
      </xsl:call-template>


      <xsl:for-each select='p3p:STATEMENT'>
	<p3pr:statement rdf:parseType="Resource">
	  <xsl:for-each select='p3p:CONSEQUENCE'>
	    <p3pr:consequence><xsl:value-of select='.'/></p3pr:consequence>
	  </xsl:for-each>


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
      <xsl:call-template name="eachPO">
        <xsl:with-param name="elt" select='"PURPOSE"'/>
        <xsl:with-param name="propName" select='"purpose"'/>
        <xsl:with-param name="prefix" select='$PurposePfx'/>
      </xsl:call-template>

	  <xsl:for-each select='p3p:DATA-GROUP/p3p:DATA'>
	    <xsl:variable name='ref' select='@ref'/>
	    <xsl:choose>
	      <xsl:when test='../@base'>
	        <xsl:message>@@we don't grok base attr on DATA-GROUP</xsl:message>
	      </xsl:when>

              <xsl:otherwise>
	        <!-- this is not what Brian did... -->
	        <p3pr:data rdf:resource='{concat($DataPfx, $ref)}'/>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
          <!-- more statement parts... @@-->
        </p3pr:statement>
      </xsl:for-each>

    </p3pr:Policy>
  </rdf:RDF>


</xsl:template>


<xsl:template name="eachPO">
  <xsl:param name="elt"/>
  <xsl:param name="propName"/>
  <xsl:param name="prefix"/>

  <xsl:message>@@eachPO</xsl:message>

  <xsl:for-each select='*[(concat(namespace-uri(), "#") = $P3P_pfx) and (local-name() = $elt)]/*'>
    <xsl:variable name="n" select='name()'/>

    <xsl:message>@@found one elt:
      ns: <xsl:value-of select='concat(namespace-uri(), "#")'/>
      p3p pfx: <xsl:value-of select='$P3P_pfx'/>
      local name: <xsl:value-of select='local-name()'/>
      elt: <xsl:value-of select='$elt'/>
    </xsl:message>

    <xsl:element name='{$propName}' namespace='{$P3P_pfx}'>
      <xsl:attribute name="rdf:resource"><xsl:value-of select='concat($prefix, $n)'/></xsl:attribute>
    </xsl:element>
  </xsl:for-each>
</xsl:template>



<!-- don't pass text thru -->
<xsl:template match="text()|@*">
</xsl:template>

</xsl:transform>
