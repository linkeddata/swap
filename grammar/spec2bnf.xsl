<xsl:transform
    xmlns:xsl ="http://www.w3.org/1999/XSL/Transform" version="1.0"
    >
<xsl:output method="text"/>

<xsl:template match="prod">
  <xsl:text>[</xsl:text>
  <xsl:value-of select="@num" />
  <xsl:text>] </xsl:text>
  <xsl:value-of select="lhs" />
  <xsl:text> ::= </xsl:text>
  <xsl:value-of select='translate(normalize-space(rhs), "&#160;", " ")' />
  <xsl:text>&#x0A;</xsl:text>
</xsl:template>

<!-- don't pass text thru -->
<xsl:template match="text()|@*">
</xsl:template>

</xsl:transform>
