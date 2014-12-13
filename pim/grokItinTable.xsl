<xsl:transform
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"  version="1.0"
  xmlns:h="http://www.w3.org/1999/xhtml"
  xmlns:r="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
  xmlns:s="http://www.w3.org/2000/01/rdf-schema#"
  xmlns:k="http://opencyc.sourceforge.net/daml/cyc.daml#"
  xmlns:t="http://www.w3.org/2000/10/swap/pim/travelTerms#"
  xmlns:dt="http://www.w3.org/2001/XMLSchema#"
  >

<!-- 

$Id$

USAGE:

1. get an HTML intinerary from AA.com or whatever, e.g. via yahoo mail
2. fix <xbody> to <body> (is that a yahoo-mail-ism?)
3. tidy -asxml trip.html >ttrip.html
4. xsltproc  grokItinTable.xsl ttrip.html  >,trip.rdf
-->


<xsl:output method="xml" indent="yes"/>

<xsl:param name='NS' select='"http://example/stuff@@#"'/>

<xsl:template match="/">
  <r:RDF>
    <r:Description r:about="">
      <k:containsInformationAbout-Focally r:parseType="Resource">
        <xsl:apply-templates/>
      </k:containsInformationAbout-Focally>
    </r:Description>
  </r:RDF>
</xsl:template>


<xsl:template match='h:tr[h:td[1] = "Date:"]'>
  <xsl:variable name='when' select='normalize-space(h:td[2])'/>
  <xsl:variable name='yyyymmdd'>
    <xsl:call-template name='grokDate'>
      <xsl:with-param name="when" select='$when'/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:message>found table row with date
     <xsl:value-of select='$when'/>
  </xsl:message>

  <xsl:variable name='carrierName' select='normalize-space(following-sibling::h:tr/h:td[2])'/>
  <xsl:variable name='flightNum' select='normalize-space(following-sibling::h:tr/h:td[3])'/>
  <!-- eqpName not used @@ -->
  <xsl:variable name='eqpName' select='normalize-space(following-sibling::h:tr/h:td[5])'/>

  <xsl:variable name='depAptName' select='normalize-space(following-sibling::h:tr[2]/h:td[2])'/>
  <xsl:variable name='depTime'>
    <xsl:call-template name='grokTime'>
      <xsl:with-param name="when"
         select='normalize-space(following-sibling::h:tr[2]/h:td[3])'/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name='depPlaceName' select='normalize-space(following-sibling::h:tr[2]/h:td[5])'/>

  <xsl:variable name='dur' select='normalize-space(following-sibling::h:tr[2]/h:td[6])'/>

  <xsl:variable name='arAptName' select='normalize-space(following-sibling::h:tr[3]/h:td[2])'/>
  <xsl:variable name='arTime'>
    <xsl:call-template name='grokTime'>
      <xsl:with-param name="when"
         select='normalize-space(following-sibling::h:tr[3]/h:td[3])'/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name='operatedBy' select='normalize-space(following-sibling::h:tr[4]/h:td[2])'/>

  <xsl:variable name='passengerName' select='normalize-space(following-sibling::h:tr[5]/h:td[2])'/>

  <xsl:variable name='seatName' select='normalize-space(following-sibling::h:tr[5]/h:td[3])'/>

  <!-- skipping: flight class, FF# -->

    <k:subEvents r:parseType="Resource">
      <k:startingDate r:parseType="Resource">
        <!-- @@convert to YYYY-MM-DD? -->
        <r:value><xsl:value-of select="$when"/></r:value>
        <dt:date><xsl:value-of select="$yyyymmdd"/></dt:date>
      </k:startingDate>

      <t:flightNumber><xsl:value-of select="$flightNum"/></t:flightNumber>
      <t:departureTime><xsl:value-of select="$depTime"/></t:departureTime>
      <t:arrivalTime><xsl:value-of select="$arTime"/></t:arrivalTime>

      <k:fromLocation>
        <k:Airport-Physical>
          <k:nameString><xsl:value-of select="$depAptName"/></k:nameString>
        </k:Airport-Physical>
      </k:fromLocation>

      <k:toLocation>
        <k:Airport-Physical>
          <k:nameString><xsl:value-of select="$arAptName"/></k:nameString>
        </k:Airport-Physical>
      </k:toLocation>

      <t:carrier r:parseType="Resource">
        <k:nameOfAgent><xsl:value-of select="$carrierName"/></k:nameOfAgent>
      </t:carrier>

      <!-- @@others -->

    </k:subEvents>

</xsl:template>

<xsl:template name="grokDate">
  <xsl:param name="when"/> <!-- format: DD MMM YY -->

  <xsl:variable name='year' select='2000 + number(substring($when, 8, 2))'/>
  <xsl:variable name='monthName' select='substring($when, 4, 3)'/>
  <xsl:variable name="month">
    <xsl:choose>
     <xsl:when test='$monthName="JAN"'>1</xsl:when>
     <xsl:when test='$monthName="FEB"'>2</xsl:when>
     <xsl:when test='$monthName="MAR"'>3</xsl:when>
     <xsl:when test='$monthName="APR"'>4</xsl:when>
     <xsl:when test='$monthName="MAY"'>5</xsl:when>
     <xsl:when test='$monthName="JUN"'>6</xsl:when>
     <xsl:when test='$monthName="JUL"'>7</xsl:when>
     <xsl:when test='$monthName="AUG"'>8</xsl:when>
     <xsl:when test='$monthName="SEP"'>9</xsl:when>
     <xsl:when test='$monthName="OCT"'>10</xsl:when>
     <xsl:when test='$monthName="NOV"'>11</xsl:when>
     <xsl:when test='$monthName="DEC"'>12</xsl:when>
   </xsl:choose>
  </xsl:variable>

  <xsl:variable name='dayOfMonth' select='number(substring($when, 1, 2))'/>

  <xsl:value-of select='concat(format-number($year, "0000"), "-", format-number(number($month), "00"), "-", format-number($dayOfMonth, "00"))'/>
</xsl:template>


<xsl:template name="grokTime">
  <xsl:param name="when"/> <!-- format: HH:MM PP -->

  <xsl:variable name='hr' select='substring-before($when, ":")'/>
  <xsl:variable name='mn' select='substring-after(substring-before($when, " "), ":")'/>
  <xsl:variable name='pmoff'>
    <xsl:choose>
      <xsl:when test='substring-after($when, " ") = "PM"'>12</xsl:when>
      <xsl:otherwise>0</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:value-of select='concat(format-number(number($hr) + number($pmoff), "00"), ":", format-number($mn, "00"))'/>
</xsl:template>

<!-- don't pass text thru -->
<xsl:template match="text()|@*">
</xsl:template>

</xsl:transform>

