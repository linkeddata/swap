<?xml version='1.0'?><!-- -*- mode: indented-text;-*- -->
<xsl:transform
    xmlns:xsl  ="http://www.w3.org/1999/XSL/Transform" version="1.0"
    xmlns:r    ="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    xmlns:s    ="http://www.w3.org/2000/01/rdf-schema#"
    xmlns:xsi  ="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:a    ="http://www.w3.org/2000/10/swap/util/applePList@@#"
    >

<xsl:output method="xml" indent="yes"/>

<xsl:variable name="RCSId"
  select='"$Id$"'/>

<xsl:variable name="P_ns"
  select='"http://www.w3.org/2000/10/swap/util/applePList@@#"'/>

<xsl:param name="Debug" select='0'/>

<!--
  http://www.apple.com/DTDs/PropertyList-1.0.dtd
  /System/Library/DTDs/PropertyList.dtd
  http://ilrt.org/discovery/chatlogs/rdfig/2002-08-05#T04-22-32
  -->

<xsl:template match="plist">
  <r:RDF>
    <xsl:apply-templates/>
  </r:RDF>
</xsl:template>

<xsl:template match="dict">
  <r:Description>
    <xsl:for-each select="key">
      <xsl:variable name='n1' select='translate(., " ", "_")'/>
      <xsl:variable name='pName'>
        <xsl:choose>
          <xsl:when test='contains("0123456789", substring($n1, 1, 1))'>
            <xsl:value-of select='concat("_", $n1)'/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select='$n1'/>
          </xsl:otherwise>
        </xsl:choose>
      </xsl:variable>

      <xsl:element namespace="{$P_ns}"
    	           name='{$pName}'>
        <xsl:for-each select='following-sibling::*[1]'>
          <xsl:choose>
            <xsl:when test='name() = "dict"'>
              <xsl:apply-templates select='.'/>
            </xsl:when>

            <xsl:when test='name() = "array"'>
              <xsl:attribute name="r:parseType">Collection</xsl:attribute>
              <xsl:apply-templates/>
            </xsl:when>

            <xsl:when test='name() = "string"'>
              <xsl:value-of select='.'/>
            </xsl:when>

            <xsl:when test='name() = "integer"'>
              <xsl:attribute name="xsi:type">integer</xsl:attribute>
              <xsl:value-of select='.'/>
            </xsl:when>

            <xsl:when test='name() = "date"'>
    	      <!-- @@check syntax details -->
              <xsl:attribute name="xsi:type">date</xsl:attribute>
              <xsl:value-of select='.'/>
            </xsl:when>

            <xsl:when test='name() = "true"'>
              <xsl:attribute name="r:resource"><xsl:value-of select='$P_ns'/>true</xsl:attribute>
            </xsl:when>

            <xsl:otherwise>
              <xsl:message>@@ <xsl:value-of select='name()'/> not impl.
              </xsl:message>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:for-each>
      </xsl:element>
    </xsl:for-each>
  </r:Description>
</xsl:template>


<!-- don't pass text thru -->
<xsl:template match="text()|@*">
</xsl:template>

</xsl:transform>
