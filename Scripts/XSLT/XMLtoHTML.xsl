<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="3.0" xmlns:tei="http://www.tei-c.org/ns/1.0">
    <xsl:output method="html"></xsl:output>
    
    <xsl:param name="page"/>
    
    
    <xsl:template match="/">
        <xsl:for-each select="//*[not(self::tei:pb)][preceding-sibling::tei:pb[1][@n=$page]]">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template match="tei:table">
        <xsl:element name="table"><xsl:apply-templates select="@* | node()"/></xsl:element>
    </xsl:template>
    
    <xsl:template match="tei:row">
        <xsl:element name="tr"><xsl:apply-templates select="@* | node()"/></xsl:element>
    </xsl:template>
    
    <xsl:template match="tei:cell">
        <xsl:choose>
            <xsl:when test="..[@role='label']">
                    <xsl:choose>
                        <xsl:when test="../tei:cell[1] = .">
                            <xsl:element name="th"><xsl:attribute name="id">author-header</xsl:attribute><xsl:apply-templates select="@* | node()"/></xsl:element>
                        </xsl:when>
                        <xsl:when test="../tei:cell[2] = .">
                            <xsl:element name="th"><xsl:attribute name="id">book-header</xsl:attribute><xsl:element name="p"><xsl:attribute name="id">category-letter</xsl:attribute><xsl:value-of select="ancestor::tei:table/tei:head/text()"/></xsl:element><xsl:element name="p"><xsl:attribute name="id">category-title</xsl:attribute><xsl:apply-templates select="@* | node()"/></xsl:element></xsl:element>
                        </xsl:when>
                        <xsl:when test="../tei:cell[3] = .">
                            <xsl:element name="th"><xsl:attribute name="id">place-header</xsl:attribute><xsl:apply-templates select="@* | node()"/></xsl:element>
                        </xsl:when>
                        <xsl:when test="../tei:cell[4] = .">
                            <xsl:element name="th"><xsl:attribute name="id">year-header</xsl:attribute><xsl:apply-templates select="@* | node()"/></xsl:element>
                        </xsl:when>
                        <xsl:when test="../tei:cell[5] = .">
                            <xsl:element name="th"><xsl:attribute name="id">folio-header</xsl:attribute><xsl:apply-templates select="@* | node()"/></xsl:element>
                        </xsl:when>
                    </xsl:choose>             
            </xsl:when>
            <xsl:otherwise>
                <xsl:element name="td"><xsl:apply-templates select="@* | node()"/></xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    
    <!-- Personen -->
    <xsl:template match="tei:persName[@key]"> <!-- Das muss ich später auf <rs> ändern -->
        <xsl:element name="span">
            <xsl:call-template name="entity-link">
                <xsl:with-param name="link-prefix">person.html?id=</xsl:with-param>
                <xsl:with-param name="id" select="./@key"/>
            </xsl:call-template>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    
    <!-- Auflagen -->
    <xsl:template match="tei:bibl[.//tei:title[@level='m']]">
        <xsl:element name="span">
            <xsl:call-template name="entity-link">
                <xsl:with-param name="link-prefix">auflage.html?id=</xsl:with-param>
                <xsl:with-param name="id" select=".//tei:rs[@type='edition']/@key"/>
            </xsl:call-template>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    
    <!-- Serien -->
    <xsl:template match="tei:title[@level='s']">
        <xsl:element name="span">
            <xsl:call-template name="entity-link">
                <xsl:with-param name="link-prefix">serie.html?id=</xsl:with-param>
                <xsl:with-param name="id" select="./@key"/>
            </xsl:call-template>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    
    <!-- Orte -->
    <xsl:template match="tei:placeName">
        <xsl:element name="span">
            <xsl:call-template name="entity-link">
                <xsl:with-param name="link-prefix">place.html?id=</xsl:with-param>
                <xsl:with-param name="id" select="./@key"/>
            </xsl:call-template>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    
    <!-- @hand -->
    <xsl:template match="@hand">
        <xsl:attribute name="data-hand">
            <xsl:value-of select="replace(., '#', '')"/>
        </xsl:attribute>
    </xsl:template>
    
    <!-- @place -->
    <xsl:template match="@place">
        <xsl:attribute name="data-place">
            <xsl:value-of select="."/>
        </xsl:attribute>
    </xsl:template>
    
    <!-- <del> -->
    <xsl:template match="tei:del">
        <xsl:element name="span">
            <xsl:attribute name="class">del</xsl:attribute>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    
    <!-- <add> oder <subst -->
    <xsl:template match="tei:add | tei:subst">
        <xsl:element name="span">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
  
    <!-- <gap> -->
    <xsl:template match="tei:gap">
        <xsl:element name="span">
            <xsl:attribute name="data-gap"><xsl:value-of select="./@quantity"/></xsl:attribute>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    
    <!-- <choice>, <abbr>, <expan> -->
    <xsl:template match="tei:choice | tei:abbr | tei:expan">
        <xsl:element name="span">
            <xsl:attribute name="class"><xsl:value-of select="./name()"/></xsl:attribute>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
  
    <xsl:template match="@*">
        <xsl:apply-templates select="@* | node()"/>
    </xsl:template>
    

    
    <xsl:template match="text()">
        <xsl:apply-templates/>
    </xsl:template>
    
    <xsl:template match="tei:add//text() | tei:cell//text()">
        <xsl:copy></xsl:copy>
    </xsl:template>
    
    
    <xsl:template name="entity-link">
        <xsl:param name="link-prefix"/>
        <xsl:param name="id"/>
        <xsl:attribute name="class">entity-link</xsl:attribute>
        <xsl:attribute name="data-ref"><xsl:value-of select="$link-prefix"/><xsl:value-of select="$id"/></xsl:attribute>
    </xsl:template>
    
</xsl:stylesheet>