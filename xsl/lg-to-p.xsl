<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    xmlns="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="xs"
    xpath-default-namespace="http://www.tei-c.org/ns/1.0"
    version="2.0">
    
    <xsl:output indent="yes"/>
    
    <xsl:template match="node() | @*">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>
    
    <xsl:template match="lg|sp">
        <xsl:copy>
            <xsl:copy-of select="@*"/>
            <xsl:for-each select="l|ab|lg|sp">
                <xsl:value-of select=".//text()/normalize-space()"/>
                <xsl:text> </xsl:text>
            </xsl:for-each>
        </xsl:copy>
    </xsl:template>
</xsl:stylesheet>
