<xsl:template match="spinner5PBuilder">
	<xsl:result-document href="{$outputfile}">
		<xsl:comment>====</xsl:comment>
		<xsl:comment>&#169; Copyright Infineon Technologies AG 2016. All rights reserved.</xsl:comment>
		<xsl:comment>DO NOT EDIT! This is generated code and will be replaced without notice.</xsl:comment>
		<xsl:comment>====</xsl:comment>
		<xsl:comment>Version of used XSLT processor: <xsl:value-of select="system-property('xsl:version')"/>
			<xsl:text> </xsl:text>
			<xsl:value-of select="system-property('xsl:vendor')"/>
			<xsl:text> </xsl:text>
			<xsl:value-of select="system-property('xsl:vendor-url')"/>
		</xsl:comment>
		<xsl:comment>
			<xsl:text>Version of used XSLT: Spec2Spirit V</xsl:text>
			<xsl:value-of select="$toolversion"/>
		</xsl:comment>
		<spirit:design>
			<xsl:attribute name="xsi:schemaLocation"><xsl:value-of select="'http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009 http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009/design.xsd'"/><!-- xsl:value-of select="' http://www.infineon.com/cms/xml/SPIRIT_IO_1685/1.0/EN http://www.infineon.com/cms/xml/SPIRIT_IO_1685/1.0/ifx_io.xsd'"/--><!-- xsl:value-of select="' http://www.w3.org/1999/02/22-rdf-syntax-ns# rdf.xsd'"/--><!-- xsl:value-of select="' http://purl.org/dc/elements/1.1/ http://dublincore.org/schemas/xmls/qdc/2008/02/11/dc.xsd'"/--></xsl:attribute>
			<spirit:vendor>IFX</spirit:vendor>
			<spirit:library>
				<xsl:value-of select="$family"/>
			</spirit:library>
			<spirit:name>
				<xsl:value-of select="$Device"/>
			</spirit:name>
			<spirit:version>
				<xsl:value-of select="$silicon_step"/>
			</spirit:version>

			<spirit:componentInstances>
				<xsl:comment>============== PIN and DEDICATED components ==============</xsl:comment>
				<!-- for each pad name in $PINS either a PIN or a DEDICATE resource is instantiated -->
				<xsl:for-each select="$PINS">
					<xsl:variable name="myname" select="." as="xs:string"/>
					<xsl:choose>
						<xsl:when test="matches(.,'^\D(\d+)_(\d+)$')">
							<spirit:componentInstance>
								<spirit:instanceName>
									<xsl:value-of select="concat('PIN_',string(position()))"/>
								</spirit:instanceName>
								<spirit:componentRef spirit:vendor="IFX" spirit:library="Platform" spirit:name="PIN" spirit:version="100"/>
								<spirit:configurableElementValues>
									<spirit:configurableElementValue spirit:referenceId="inst">
										<xsl:value-of select="position()"/>
									</spirit:configurableElementValue>
									<spirit:configurableElementValue spirit:referenceId="name">
										<xsl:value-of select="$myname"/>
									</spirit:configurableElementValue>
									<spirit:configurableElementValue spirit:referenceId="displayName">
										<xsl:choose>
											<xsl:when test="root()/spinner5PBuilder/ioPad[@name = $myname]/properties/Diagram_Label">
												<xsl:value-of select="normalize-space(root()/spinner5PBuilder/ioPad[@name = $myname]/properties/Diagram_Label)" disable-output-escaping="no"/>
											</xsl:when>
											<xsl:otherwise>
												<xsl:value-of select="translate($myname,'_','.')"/>
											</xsl:otherwise>
										</xsl:choose>
									</spirit:configurableElementValue>
									<xsl:variable name="numbers" select="tokenize(replace(.,'^\D(\d+)_(\d+)$','$1,$2'),',')"/>
									<spirit:configurableElementValue spirit:referenceId="port">
										<xsl:value-of select="f:str2dec($numbers[1])"/>
									</spirit:configurableElementValue>
									<spirit:configurableElementValue spirit:referenceId="bit">
										<xsl:value-of select="f:str2dec($numbers[2])"/>
									</spirit:configurableElementValue>
									<xsl:if test="matches(root()/spinner5PBuilder/ioPad[@name = $myname]/properties/Diagram_Label/text(),' AN\d')">
										<spirit:configurableElementValue spirit:referenceId="_ANARES">
											<xsl:value-of select="replace(root()/spinner5PBuilder/ioPad[@name = $myname]/properties/Diagram_Label/text(),'^.* (AN\d+).*$','$1')"/>
										</spirit:configurableElementValue>
									</xsl:if>
									<xsl:for-each select="$ParaMaps2/*/*[local-name()='Mutex' and translate(string(@ref),'.','_') = $myname]">
										<spirit:configurableElementValue spirit:referenceId="_group">
											<xsl:value-of select="."/>
										</spirit:configurableElementValue>
									</xsl:for-each>
								</spirit:configurableElementValues>
							</spirit:componentInstance>
						</xsl:when>
						<xsl:otherwise>
							<spirit:componentInstance>
								<spirit:instanceName>
									<xsl:value-of select="concat('DEDICATED_',string(position()))"/>
								</spirit:instanceName>
								<spirit:componentRef spirit:vendor="IFX" spirit:library="Platform" spirit:name="DEDICATED" spirit:version="100"/>
								<spirit:configurableElementValues>
									<spirit:configurableElementValue spirit:referenceId="inst">
										<xsl:value-of select="position()"/>
									</spirit:configurableElementValue>
									<spirit:configurableElementValue spirit:referenceId="name">
										<xsl:value-of select="$myname"/>
										<xsl:if test="root()/spinner5PBuilder/ioPad[ends-with(@name,current())]/properties/Polarity='ActiveLow'">_n</xsl:if> 
									</spirit:configurableElementValue>
									<spirit:configurableElementValue spirit:referenceId="displayName">
										<xsl:choose>
											<xsl:when test="root()/spinner5PBuilder/ioPad[ends-with(@name,current())]/properties/Diagram_Label">
												<xsl:value-of select="normalize-space(root()/spinner5PBuilder/ioPad[ends-with(@name,current())]/properties/Diagram_Label)" disable-output-escaping="no"/>
											</xsl:when>
											<xsl:when test="root()/spinner5PBuilder/ioPad[ends-with(@name,current())]/properties/Polarity='ActiveLow'">
												<xsl:value-of select="'&lt;Negation&gt;'"/>
												<xsl:value-of select="."/>
												<xsl:value-of select="'&lt;/Negation&gt;'"/>
											</xsl:when>
											<xsl:otherwise>
												<xsl:value-of select="."/>
											</xsl:otherwise>
										</xsl:choose>
									</spirit:configurableElementValue>
									<xsl:for-each select="$ParaMaps2/*/*[local-name()='Mutex' and translate(string(@ref),'.','_') = $myname]">
										<spirit:configurableElementValue spirit:referenceId="_group">
											<xsl:value-of select="."/>
										</spirit:configurableElementValue>
									</xsl:for-each>
								</spirit:configurableElementValues>
							</spirit:componentInstance>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:for-each>
				<xsl:for-each-group select="$ParaMaps2/*" group-by="local-name()">
					<xsl:choose>
						<xsl:when test="current-grouping-key()='PIN'"/>
						<xsl:when test="current-grouping-key()='DEDICATED'"/>
						<xsl:when test="ends-with(current-grouping-key(),'spec')"/>
						<xsl:otherwise>
							<xsl:variable name="map" select="$ParaMaps2/*[local-name()=concat(current-grouping-key(),'spec')]"/>
							<xsl:comment>============== <xsl:value-of select="current-grouping-key()"/> subcomponents ==============</xsl:comment>
							<xsl:for-each-group select="current-group()" group-by="*[local-name()='ParamDecl' and @Name='inst']/*[local-name()='Value']">						
								<xsl:variable name="instance" select="current-group()[1]"/>
								<xsl:for-each select="$map/*[local-name()='Resource']">
									<xsl:copy-of select="f:makeResourceInstance(.,$instance/@Int_Class_ID)"/>
								</xsl:for-each>						
							</xsl:for-each-group>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:for-each-group>
			</spirit:componentInstances>


			<spirit:adHocConnections>
				<xsl:comment>============== PIN/DEDICATED connections ==============</xsl:comment>
				<xsl:for-each select="ioPad">
					<xsl:sort select="@name" data-type="number"/>
					<xsl:variable name="inst" select="f:locatePin(@name)"/>
					<xsl:variable name="name" select="@name"/>
					<xsl:if test="matches($inst,'^DEDICATED_(\d+)$')">
						<xsl:comment><xsl:value-of select="$name"/>: <xsl:value-of select="$inst"/> outputs</xsl:comment>
						<xsl:for-each select="hdlInfo/Mode[starts-with(@type,'O') and properties/Function/text() !='Test']">
							<xsl:variable name="drivers" select="f:name2Driver(reference/ComponentPinRef/@name,'DEDICATED')" as="item()*"/>
							<xsl:if test="count($drivers)">
								<spirit:adHocConnection>
									<spirit:name>
										<xsl:value-of select="concat($inst,'_IN')"/>
									</spirit:name>
									<spirit:description>
										<xsl:value-of select="concat(reference/ComponentPinRef/@name,'__',$name,'_OUT')"/>
									</spirit:description>
									<spirit:internalPortReference>
										<xsl:attribute name="spirit:componentRef" select="$inst"/>
										<xsl:attribute name="spirit:portRef" select="'IN'"/>
									</spirit:internalPortReference>
									<xsl:copy-of select="$drivers"/>
								</spirit:adHocConnection>
							</xsl:if>
						</xsl:for-each>
					</xsl:if>
					<xsl:if test="matches($inst,'^PIN_(\d+)$')">
						<xsl:variable name="numbers" select="tokenize(replace($name,'^\D(\d+)_(\d+)$','$1,$2'),',')"/>
						<xsl:comment><xsl:value-of select="$name"/>: <xsl:value-of select="$inst"/> output multiplexer</xsl:comment>
						<xsl:for-each select="hdlInfo/Mode[(starts-with(@type,'O') and @number!=0) and properties/Function/text() !='Test']">
							<xsl:variable name="alt" select="@number"/>
							<xsl:choose>
								<xsl:when test="starts-with(reference/ComponentPinRef/@name,'IOM_')"/><!-- wrong direction in Spirit due to queer topology -->
								<xsl:otherwise>
									<spirit:adHocConnection>
										<spirit:name>
											<xsl:value-of select="concat($inst,'_ALT',@number)"/>
										</spirit:name>
										<spirit:description>
											<xsl:value-of select="concat(replace(reference/ComponentPinRef/@name,'^suppress_',''),'__',$name,'_OUT')"/>
										</spirit:description>
										<spirit:internalPortReference>
											<xsl:attribute name="spirit:componentRef" select="$inst"/>
											<xsl:attribute name="spirit:portRef" select="concat('ALT',@number)"/>
										</spirit:internalPortReference>
										<xsl:copy-of select="f:name2Driver(reference/ComponentPinRef/@name,'PIN')"/>
									</spirit:adHocConnection>	
								</xsl:otherwise>
							</xsl:choose>								
						</xsl:for-each>
					</xsl:if>
					<xsl:if test="string-length($inst)">
						<xsl:variable name="hwOuts">
							<xsl:for-each select="hdlInfo/Mode[(starts-with(@type,'HW') or string(@type)='DIRECT_OUT') and properties/Function/text() !='Test']">
								<xsl:variable name="drivers" select="f:name2Driver(reference/ComponentPinRef/@name,replace($inst,'_.*$',''))" as="item()*"/>
								<xsl:if test="count($drivers)">
									<spirit:description>
										<xsl:value-of select="concat(reference/ComponentPinRef/@name,'__',$name,'_OUT')"/>
									</spirit:description>
									<xsl:copy-of select="$drivers"/>
								</xsl:if>
							</xsl:for-each>
						</xsl:variable>
						<xsl:for-each select="$hwOuts/spirit:description">
							<xsl:variable name="group" select="position()"/>
							<spirit:adHocConnection>
								<spirit:name>
									<xsl:value-of select="concat($inst,'_HWOUT',$group)"/>
								</spirit:name>
								<xsl:copy-of select="."/>
								<spirit:internalPortReference>
									<xsl:attribute name="spirit:componentRef" select="$inst"/>
									<xsl:attribute name="spirit:portRef" select="concat('HWOUT',$group)"/>
								</spirit:internalPortReference>
								<xsl:copy-of select="following-sibling::spirit:internalPortReference[preceding-sibling::spirit:description[1] = $hwOuts/spirit:description[$group]]"/>
							</spirit:adHocConnection>
						</xsl:for-each>
						<xsl:for-each select="$hwOuts/spirit:comment">
							<xsl:comment>
								<xsl:value-of select="."/>
							</xsl:comment>
						</xsl:for-each>
						<xsl:for-each select="hdlInfo/Mode[starts-with(@type,'R') and properties/Function/text() !='Test']">
							<xsl:variable name="analog" select="f:name2Driver(reference/ComponentPinRef/@name,'AN')"/>
							<xsl:variable name="anares" select="reference/ComponentPinRef/@name"/>
							<xsl:choose>
								<xsl:when test="properties/Direction/text()='Out'">
									<spirit:adHocConnection>
										<spirit:name>
											<xsl:value-of select="concat($inst,'_AN')"/>
											<xsl:value-of select="concat($analog//@spirit:componentRef,'_',$analog//@spirit:portRef)"/>
										</spirit:name>
										<spirit:description>
											<xsl:value-of select="concat($anares,'__',$name,'_AN')"/>
										</spirit:description>
										<spirit:internalPortReference>
											<xsl:attribute name="spirit:componentRef" select="$inst"/>
											<xsl:attribute name="spirit:portRef" select="'ANARES'"/>
										</spirit:internalPortReference>
										<xsl:copy-of select="$analog"/>
									</spirit:adHocConnection>	
								</xsl:when>
								<xsl:otherwise>
									<xsl:for-each select="$analog">
										<spirit:adHocConnection>
											<spirit:name>
												<xsl:value-of select="concat(@spirit:componentRef,'_',@spirit:portRef)"/>
											</spirit:name>
											<spirit:description>
												<xsl:value-of select="concat($name,'_AN__',$anares)"/>
											</spirit:description>
											<xsl:copy-of select="."/>
											<spirit:internalPortReference>
												<xsl:attribute name="spirit:componentRef" select="$inst"/>
												<xsl:attribute name="spirit:portRef" select="'ANARES'"/>
											</spirit:internalPortReference>
										</spirit:adHocConnection>	
									</xsl:for-each>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:for-each>
					</xsl:if>
				</xsl:for-each>
				<xsl:for-each-group select="$ParaMaps2/*" group-by="local-name()">
					<xsl:choose>
						<xsl:when test="current-grouping-key()='PIN'"/>
						<xsl:when test="current-grouping-key()='DEDICATED'"/>
						<xsl:when test="ends-with(current-grouping-key(),'spec')"/>
						<xsl:otherwise>
							<xsl:variable name="map" select="$ParaMaps2/*[local-name()=concat(current-grouping-key(),'spec')]"/>
							<xsl:for-each-group select="current-group()" group-by="*[local-name()='ParamDecl' and @Name='inst']/*[local-name()='Value']/text()">						
								<xsl:for-each select="current-group()">						
									<xsl:variable name="instance" select="."/>
									<xsl:variable name="conceptinst" select="upper-case(@Int_Class_ID)"/>
									<xsl:comment>============== <xsl:value-of select="$conceptinst"/> connections ==============</xsl:comment>
									<xsl:for-each select="$Connects[upper-case(*[local-name()='in']/*[local-name()='ConceptInstanceName']/text())=$conceptinst]">
										<xsl:copy-of select="f:makeNet(.,$instance)"/>
									</xsl:for-each>
									<xsl:for-each select="$Connects[upper-case(*[local-name()='in']/*[local-name()='ConceptInstanceName']/text())=$conceptinst and @socket]">
										<xsl:variable name="context" select="upper-case(./*[local-name()='out']/*[local-name()='ConceptInstanceName']/text())"/>
										<xsl:choose>
											<xsl:when test="$ParaMaps2/key('instance',$context)">													
												<xsl:variable name="me" select="."/>
												<xsl:for-each select="$ParaMaps2/key('instance',$context)">
													<xsl:copy-of select="f:makeSocketNets($me,$instance,.)"/>
												</xsl:for-each>
											</xsl:when>
											<xsl:otherwise>
												<!-- xsl:comment>Socketconnection <xsl:value-of select="$context"/> -> <xsl:value-of select="$instance/@Int_Class_ID"/> skipped</xsl:comment -->
											</xsl:otherwise>
										</xsl:choose>
									</xsl:for-each>
									<xsl:if test="local-name()='CAN'"><!-- TODO make this via alias names in map? -->
										<xsl:for-each select="for $node in 1 to xs:integer($instance/*[local-name()='ParamDecl' and @Name='MCMCAN_N_NODE']/*[local-name()='Value']/text()) return xs:integer($node - 1)">
											<xsl:for-each select="$Connects[upper-case(*[local-name()='in']/*[local-name()='ConceptInstanceName']/text())=concat($conceptinst,current())]">
												<xsl:copy-of select="f:makeNet(.,$instance)"/>
											</xsl:for-each>
										</xsl:for-each>
									</xsl:if>
								</xsl:for-each>
								<xsl:variable name="instance" select="current-group()[1]"/>
								<xsl:for-each select="$map/*[local-name()='Net']">
									<xsl:copy-of select="f:makeNetInstance(.,$instance)"/>
								</xsl:for-each>
							</xsl:for-each-group>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:for-each-group>
			</spirit:adHocConnections>
			<spirit:vendorExtensions>
				<xsl:call-template name="MetaData"/>
			</spirit:vendorExtensions>
		</spirit:design>
	</xsl:result-document>
</xsl:template>