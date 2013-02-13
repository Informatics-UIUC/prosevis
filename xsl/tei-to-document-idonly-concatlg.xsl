<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="2.0"
    xmlns:seasr="http://www.seasr.org/ns/services/openmary/tei/1.0"
    xpath-default-namespace="http://www.tei-c.org/ns/1.0">

    <xsl:output indent="yes"/>
        
    <xsl:template match="/">
        <document>
            <xsl:apply-templates select="/TEI/text/body"/>
        </document>
    </xsl:template>
    
    <xsl:template match="p|lg|sp">
        <xsl:element name="{local-name()}">
            <xsl:copy-of select="@seasr:id"/>
            <xsl:attribute name="seasr:sid">
                <xsl:choose>
                    <xsl:when test="exists(parent::node()[starts-with(name(), 'div')])">
                        <xsl:value-of select="parent::node()/@seasr:sid"/>
                    </xsl:when>
                </xsl:choose>
            </xsl:attribute>
            
            <xsl:value-of select=".//text()/normalize-space()"/>
        </xsl:element>
    </xsl:template>
    
    <xsl:template match="text()"/>
</xsl:stylesheet>

