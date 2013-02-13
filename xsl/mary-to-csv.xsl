<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema" exclude-result-prefixes="xs"
    xmlns:mary="http://mary.dfki.de/2002/MaryXML" version="2.0">
    
    <xsl:output method="text"/>
    
    <xsl:variable name="separator">
        <xsl:text>&#x9;</xsl:text>
    </xsl:variable>
    
    <xsl:template match="mary:maryxml">
        <xsl:call-template name="writeTableHeader"/>
        
        <xsl:for-each select="mary:p">
            <xsl:variable name="pid" select="position()"/>
            <xsl:for-each select="mary:voice/mary:s">
                <xsl:variable name="sid" select="position()"/>
                <xsl:for-each select="descendant-or-self::mary:phrase">
                    <xsl:variable name="phid" select="position()"/>
                    <xsl:for-each select="descendant-or-self::mary:t">
                        <xsl:variable name="t" select="."/>
                        <xsl:if test="string($t)">
                            <xsl:choose>
                                <xsl:when test="exists(@ph)">
                                    <xsl:for-each select="tokenize(@ph,'-')">
                                        <xsl:call-template name="writeTableEntry">
                                            <xsl:with-param name="pid" select="$pid"/>
                                            <xsl:with-param name="sid" select="$sid"/>
                                            <xsl:with-param name="phid" select="$phid"/>
                                            <xsl:with-param name="t" select="$t"/>
                                            <xsl:with-param name="stress" select='number(matches(., ".*&apos;.*"))'/>
                                            <xsl:with-param name="ph" select='normalize-space(replace(., "&apos;", ""))'/>
                                        </xsl:call-template>
                                    </xsl:for-each>
                                </xsl:when>
                                <xsl:otherwise>
                                    <xsl:call-template name="writeTableEntry">
                                        <xsl:with-param name="pid" select="$pid"/>
                                        <xsl:with-param name="sid" select="$sid"/>
                                        <xsl:with-param name="phid" select="$phid"/>
                                        <xsl:with-param name="t" select="$t"/>
                                        <xsl:with-param name="stress" select="string('')"/>
                                        <xsl:with-param name="ph" select="string('')"/>
                                    </xsl:call-template>
                                </xsl:otherwise>
                            </xsl:choose>
                        </xsl:if>
                    </xsl:for-each>
                </xsl:for-each>
            </xsl:for-each>
        </xsl:for-each>
    </xsl:template>
    
    <xsl:template name="writeTableHeader">
        <xsl:text>paragraph_id</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>sentence_id</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>phrase_id</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>word</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>part_of_speech</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>accent</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>phoneme</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>stress</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>tone</xsl:text>
        <xsl:value-of select="$separator"/>
        <xsl:text>break_index</xsl:text>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>
    
    <xsl:template name="writeTableEntry">
        <xsl:param name="pid"/>
        <xsl:param name="sid"/>
        <xsl:param name="phid"/>
        <xsl:param name="t"/>
        <xsl:param name="stress"/>
        <xsl:param name="ph"/>
        
        <xsl:value-of select="$pid"/>
        <xsl:value-of select="$separator"/>
        <xsl:value-of select="$sid"/>
        <xsl:value-of select="$separator"/>
        <xsl:value-of select="$phid"/>
        <xsl:value-of select="$separator"/>
        <xsl:choose>
            <xsl:when test="exists($t/parent::mary:mtu[@orig])">
                <xsl:value-of select="normalize-space($t/parent::mary:mtu/@orig)"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="normalize-space($t/text())"/>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:value-of select="$separator"/>
        <xsl:value-of select="$t/@pos"/>
        <xsl:value-of select="$separator"/>
        <xsl:value-of select="$t/@accent"/>
        <xsl:value-of select="$separator"/>
        <xsl:value-of select="$ph"/>
        <xsl:value-of select="$separator"/>
        <xsl:value-of select="$stress"/>
        <xsl:value-of select="$separator"/>
        <xsl:variable name="boundary" select="$t/ancestor::mary:phrase//mary:boundary"/>
        <xsl:value-of select="$boundary/@tone"/>
        <xsl:value-of select="$separator"/>
        <xsl:value-of select="$boundary/@breakindex"/>
        <xsl:text>&#xa;</xsl:text>
    </xsl:template>
    
</xsl:stylesheet>
