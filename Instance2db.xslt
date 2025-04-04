<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:f="http://www.infineon.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" exclude-result-prefixes="#all">
	<!--	================================================================================	-->
	<!-- Started by IFAG BEX RDE DOC, Harry Siebert  -->
	<!-- Infineon Technologies AG, Documentation Methodologies	 -->
	<!--	-->
	<!--	This XSLT transforms an Instance Sheet from a SBF XML file into an intermediate database XML-File.	-->
	<!--	-->
	<xsl:param name="toolversion" select="'1.4'"/>
	<!--	Version History:	-->
	<!--	V1.4	Sorting within group with same key added -->
	<!--	V1.3	xsi:type added for InstanceSheet elements -->
	<!--	V1.2	Parameter FilterParams added -->
	<!--	V1.1	Selectable Sockets added	-->
	<!--	V1.0	First release	-->
	<!--	-->
	<xsl:param name="debug" select="'0'"/>
	<!--	=========================  XSLT parameter Platform mode ======================	-->
	<xsl:param name="IProot" select="'C:\Users\siebert\siebert_sbf_sockets_current\var\vob\sbf\sbf\vob\sbf_resources\'"/>
	<xsl:param name="Filter"/>
	<!-- match pattern for Silicon selection -->
	<xsl:param name="extracolumns" select="'|SpiritClass|'"/>
	<!--	-->
	<!-- Windows-path to the virtual root of the paths given in the index file -->
	<xsl:param name="drive" select="'file:'"/>
	<!--xsl:param name="drive" select="'file://ccm.vih.infineon.com/rmrepo/pool1/config'"/-->
	<!-- Unix-path to the virtual root of the paths given in the index file -->
	<xsl:param name="disc" select="'file:'"/>
	<!--xsl:param name="disc" select="'/var/vob/ccm/config/vob/config'"/-->
	<xsl:param name="FilterParams" as="xs:string" select="'audience platform product package props otherprops'"/>
	<xsl:variable name="filterparams" as="xs:string*" select="tokenize($FilterParams,'[&quot;\s]+')"/>
	<!--	=========================  XSLT parameter processing ======================	-->
	<xsl:variable name="effectiveFilter" as="xs:string">
		<xsl:choose>
			<xsl:when test="string-length($Filter)">
				<xsl:value-of select="$Filter"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="//SbfInstanceDefinition/DefaultSilicon"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:variable>
	<!-- -->
	<xsl:function name="f:cleanFileName" as="xs:string">
		<xsl:param name="raw" as="xs:string"/>
		<xsl:value-of select="replace(replace(translate($raw,'\','/'),'^file:/+(\D:)','$1'),'^file:/+','//')"/>
	</xsl:function>
	<!-- load look up list -->
	<xsl:variable name="LookUpList">
		<xsl:for-each select="tokenize(translate($IProot,'\','/'),',')">
			<xsl:choose>
				<xsl:when test="ends-with(.,'/')"/>
				<xsl:when test="not(doc-available(.))">
					<xsl:message select="concat('Cannot open Lookup File ',.)" terminate="no"/>
				</xsl:when>
				<xsl:when test="document(.)//*:RelMgrLookup">
					<xsl:for-each-group select="document(.)//*:file" group-by="@key">
						<xsl:for-each-group select="current-group()" group-by="@level">
							<xsl:sort select="current-grouping-key()" order="ascending" data-type="number"/>
							<xsl:if test="position()=1">
								<xsl:for-each select="current-group()">
									<xsl:sort select="f:stuffDigits(../@Version)" order="descending"/>
									<xsl:copy>
										<xsl:copy-of select="@*|../@*"/>
										<xsl:value-of select="replace(text(),$drive,$disc)"/>
									</xsl:copy>
								</xsl:for-each>
							</xsl:if>
						</xsl:for-each-group>
					</xsl:for-each-group>
				</xsl:when>
			</xsl:choose>
		</xsl:for-each>
	</xsl:variable>
	<xsl:function name="f:stuffDigits">
		<xsl:param name="in" as="xs:string"/>
		<xsl:value-of select="replace(replace($in,'\.(\d)(\.|$)','.0$1$2'),'(\.|V)(\d)(\.|$)','$10$2$3')"/>
	</xsl:function>
	<!-- file lookup: Either absolute path or "V:L:N:V" -->
	<xsl:function name="f:resolvePath2" as="xs:string">
		<xsl:param name="key" as="xs:string"/>
		<xsl:value-of select="f:resolvePath2($key,0)"/>
	</xsl:function>
	<xsl:function name="f:resolvePath2" as="xs:string">
		<xsl:param name="key" as="xs:string"/>
		<xsl:param name="withSubdir" as="xs:integer"/>
		<xsl:variable name="file" as="xs:string">
			<xsl:choose>
				<xsl:when test="ends-with(normalize-space($key),'.xml')">
					<xsl:value-of select="normalize-space($key)"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="concat(translate($key,':','_'),'.xml')"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:variable name="files" as="xs:string*">
			<xsl:for-each select="tokenize(translate($IProot,'\','/'),',')">
				<xsl:choose>
					<xsl:when test="ends-with(.,$file)">
						<xsl:value-of select="."/>
					</xsl:when>
					<xsl:when test="ends-with(.,'/')">
						<xsl:variable name="this" select="concat(normalize-space(.),$file)"/>
						<xsl:if test="doc-available($this)">
							<xsl:value-of select="$this"/>
						</xsl:if>
					</xsl:when>
				</xsl:choose>
			</xsl:for-each>
			<xsl:if test="$withSubdir=1">
				<xsl:variable name="subkeys" as="xs:string*" select="tokenize(upper-case($effectiveFilter),'/')"/>
				<xsl:variable name="submatched" as="item()*">
					<xsl:for-each select="$LookUpList/*:file[@key=$key]">
						<xsl:variable name="mykeys" as="xs:string*" select="tokenize(upper-case(substring-before(substring-after(text(),'/lnk/'),'/')),'-')"/>
						<xsl:copy>
							<xsl:attribute name="dir_level">
								<xsl:choose>
									<xsl:when test="count($mykeys)=0">0</xsl:when>
									<xsl:when test="count($subkeys) &lt; count($mykeys)">-1</xsl:when>
									<xsl:when test="$subkeys[1] != $mykeys[1]">-1</xsl:when>
									<xsl:when test="count($mykeys)=1">1</xsl:when>
									<xsl:when test="$subkeys[2] != $mykeys[2]">-1</xsl:when>
									<xsl:when test="count($mykeys)=2">2</xsl:when>
									<xsl:when test="$subkeys[3] != $mykeys[3]">-1</xsl:when>
									<xsl:otherwise>3</xsl:otherwise>
								</xsl:choose>
							</xsl:attribute>
							<xsl:copy-of select="@*|../@*|text()"/>
						</xsl:copy>
					</xsl:for-each>
				</xsl:variable>
				<xsl:for-each select="$submatched[@dir_level &gt;= 0]">
					<xsl:sort select="@dir_level" order="descending" data-type="number"/>
					<xsl:copy-of select="."/>
				</xsl:for-each>
			</xsl:if>
			<xsl:if test="$withSubdir=0">
				<xsl:for-each select="$LookUpList/*:file[@key=$key]">
					<xsl:value-of select="text()"/>
				</xsl:for-each>
			</xsl:if>
			<xsl:value-of select="normalize-space($file)"/>
		</xsl:variable>
		<xsl:value-of select="$files[1]"/>
	</xsl:function>
	<!-- -->
	<!--	========================= library functions ======================	-->
	<xsl:include href="./mathlib2.xslt"/>
	<!--	========================= Initialization ======================	-->
	<!-- collect global parameters from Excel common sheet -->
	<xsl:variable name="Commons" select="//SbfInstanceDefinition/ParameterMap[not($filterparams=Name/text())]"/>
	<xsl:variable name="DefaultFilters" select="//SbfInstanceDefinition/ParameterMap[$filterparams=Name/text()]"/>
	<!-- collect default parameters and interface details from all referenced IPs -->
	<xsl:variable name="IPdefs">
		<xsl:variable name="IPrefs">
			<xsl:for-each select="//Instance[not(./Silicon) or contains(string-join(('|',./Silicon/text(),'|'),'|'),concat('|',$effectiveFilter,'|'))]">
				<key>
					<xsl:value-of select="f:makeKey(VLNV)"/>
				</key>
			</xsl:for-each>
		</xsl:variable>
		<xsl:for-each-group select="$IPrefs/key" group-by=".">
			<xsl:variable name="file" select="f:resolvePath2(current-grouping-key(),1)"/>
			<xsl:if test="doc-available($file)">
				<xsl:variable name="source" select="document($file)"/>
				<Parameters>
					<xsl:attribute name="key" select="current-grouping-key()"/>
					<xsl:copy-of select="$source//ParamDeclBlock/ParamDecl"/>
					<xsl:copy-of select="$source//GenericDeclBlock/GenericDecl"/>
				</Parameters>
				<Interfaces>
					<xsl:attribute name="key" select="current-grouping-key()"/>
					<xsl:copy-of select="$source//Interface"/>
				</Interfaces>
				<RegMemSets>
					<xsl:attribute name="key" select="current-grouping-key()"/>
					<xsl:copy-of select="$source//RegMemSet"/>
				</RegMemSets>
				<Modes>
					<xsl:attribute name="key" select="current-grouping-key()"/>
					<xsl:copy-of select="$source//BitFieldElement/AccessLevel"/>
					<xsl:copy-of select="$source//BitFieldSequenceElement/AccessLevel"/>
					<xsl:copy-of select="$source//Interface//AccessCondition"/>
				</Modes>
			</xsl:if>
			<xsl:if test="not(doc-available($file))">
				<xsl:message terminate="no">Missing component definition: <xsl:value-of select="$file"/>
				</xsl:message>
			</xsl:if>
		</xsl:for-each-group>
	</xsl:variable>
	<!-- map parameters of all instances -->
	<xsl:variable name="ParaMaps2" as="item()*">
		<parameter>
			<xsl:attribute name="Int_Class_ID" select="'0'"/>
			<xsl:for-each select="//Component/ParamDeclBlock/ParamDecl|//Component/ConstDefBlock/ConstDef|//Component/GenericDeclBlock/GenericDecl">
				<xsl:variable name="pn" select="Name/text()"/>
				<xsl:copy>
					<xsl:attribute name="Name" select="$pn"/>
					<xsl:copy-of select="@*"/>
					<xsl:copy-of select="*"/>
				</xsl:copy>
			</xsl:for-each>
		</parameter>
		<xsl:for-each select="//Instance[not(./Silicon) or contains(string-join(('|',./Silicon/text(),'|'),'|'),concat('|',$effectiveFilter,'|'))]">
			<xsl:variable name="raw" as="item()*">
				<xsl:variable name="key" select="f:makeKey(VLNV)"/>
				<xsl:call-template name="paraMaps">
					<xsl:with-param name="inst" select="./Int_Class_ID"/>
				</xsl:call-template>
				<xsl:copy-of select="$Commons"/>
				<xsl:copy-of select="$IPdefs/Parameters[@key=$key]/ParamDecl"/>
			</xsl:variable>
			<filter>
				<xsl:attribute name="Int_Class_ID" select="./Int_Class_ID"/>
				<xsl:for-each select="$filterparams">
					<xsl:variable name="pn" select="."/>
					<xsl:choose>
						<xsl:when test="count($raw[local-name()='ParameterMap' and ./Name=$pn])">
							<xsl:variable name="merged" as="xs:string*">
								<xsl:variable name="all" select="replace(string-join(($raw[local-name()='ParameterMap' and ./Name=$pn]/Value/text()),' '),'&quot;',' ')"/>
								<xsl:for-each-group select="tokenize(normalize-space($all),' ')" group-by=".">
									<xsl:value-of select="current-grouping-key()"/>
								</xsl:for-each-group>
							</xsl:variable>
							<ParamDecl xsi:type="StringDecl">
								<xsl:attribute name="Name" select="$pn"/>
								<Name>
									<xsl:value-of select="$pn"/>
								</Name>
								<Value>
									<xsl:value-of select="string-join(($merged),' ')"/>
								</Value>
							</ParamDecl>
						</xsl:when>
						<xsl:otherwise>
							<xsl:for-each select="$raw[local-name()='ParamDecl' and ./Name=$pn]">
								<xsl:copy>
									<xsl:attribute name="Name" select="$pn"/>
									<xsl:copy-of select="@*|*"/>
									<Value>
										<xsl:value-of select="DefaultValue/text()"/>
									</Value>
								</xsl:copy>
							</xsl:for-each>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:for-each>
			</filter>
			<parameter>
				<xsl:attribute name="Int_Class_ID" select="./Int_Class_ID"/>
				<xsl:for-each select="$raw[local-name()='ParamDecl' and not($filterparams=./Name/text())]">
					<xsl:variable name="pn" select="./Name/text()"/>
					<xsl:copy>
						<xsl:attribute name="Name" select="$pn"/>
						<xsl:copy-of select="@*|*"/>
						<Value>
							<xsl:choose>
								<xsl:when test="$raw[local-name()='ParameterMap' and ./Name=$pn]">
									<xsl:value-of select="$raw[local-name()='ParameterMap' and ./Name=$pn][1]/Value"/>
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of select="DefaultValue/text()"/>
								</xsl:otherwise>
							</xsl:choose>
						</Value>
					</xsl:copy>
				</xsl:for-each>
			</parameter>
		</xsl:for-each>
	</xsl:variable>
	<xsl:template name="paraMaps">
		<xsl:param name="inst"/>
		<xsl:copy-of select="//Instance[Int_Class_ID = $inst]/ParameterMap"/>
		<xsl:for-each select="//Instance[Int_Class_ID = $inst]/BusInstanceReference/BusInterfaceMap">
			<xsl:choose>
				<xsl:when test="(@type,@xsi:type)='BusSlaveInterfaceMap'">
					<ParameterMap>
						<Name>
							<xsl:value-of select="concat(Interface,'_base')"/>
						</Name>
						<Type>INTEGER</Type>
						<Value>
							<xsl:value-of select="StartAddress"/>
						</Value>
					</ParameterMap>
					<ParameterMap>
						<Name>
							<xsl:value-of select="concat(Interface,'_range')"/>
						</Name>
						<Type>INTEGER</Type>
						<Value>0x<xsl:value-of select="f:decimal-to-hex(f:integerEssence(EndAddress/text()) - f:integerEssence(StartAddress/text()) + 1)"/>
						</Value>
					</ParameterMap>
				</xsl:when>
				<xsl:when test="(@type,@xsi:type)='BusMasterInterfaceMap' and StartAddress">
					<xsl:variable name="key" select="f:makeKey(//Instance[Int_Class_ID = $inst]/VLNV)"/>
					<xsl:variable name="targetAdr" select="StartAddress/text()"/>
					<xsl:variable name="myname" select="Interface/text()"/>
					<!-- the target offset is given in Mapping for the Master role but must be named with the associated Slave role -->
					<xsl:variable name="masterID" as="xs:string*">
						<!-- get ID of master interface -->
						<xsl:for-each select="$IPdefs/Interfaces[@key=$key]/Interface[Role = 'Master']">
							<!-- TODO:  and f:booleanEssence(Hidden) = 0 -->
							<xsl:variable name="design">
								<xsl:call-template name="guessName"/>
							</xsl:variable>
							<xsl:if test="$design = $myname">
								<xsl:value-of select="ID"/>
							</xsl:if>
						</xsl:for-each>
						<xsl:value-of select="'unknown'"/>
						<!-- ECB file inconsistent or buggy -->
					</xsl:variable>
					<xsl:for-each select="$IPdefs/Interfaces[@key=$key]/Interface[AddressBlock/XRefMasterInterface/XRefTargetID = $masterID[1]]">
						<!-- find slave interfaces -->
						<xsl:variable name="design">
							<xsl:call-template name="guessName"/>
						</xsl:variable>
						<ParameterMap>
							<Name>
								<xsl:value-of select="concat($design,'_dest')"/>
							</Name>
							<Type>INTEGER</Type>
							<Value>
								<xsl:value-of select="$targetAdr"/>
							</Value>
						</ParameterMap>
					</xsl:for-each>
				</xsl:when>
			</xsl:choose>
		</xsl:for-each>
		<xsl:variable name="ref" select="//Instance[Int_Class_ID = $inst]/ComponentInstanceReference[not(./Silicon) or contains(string-join(('|',./Silicon/text(),'|'),'|'),concat('|',$effectiveFilter,'|'))]/ComponentInstanceRef"/>
		<xsl:if test="//Instance[Int_Class_ID = $ref]">
			<xsl:call-template name="paraMaps">
				<xsl:with-param name="inst" select="$ref"/>
			</xsl:call-template>
		</xsl:if>
	</xsl:template>
	<xsl:template name="guessName">
		<xsl:choose>
			<xsl:when test="string-length(Name) &gt; 0">
				<xsl:value-of select="Name"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="lower-case(ExtVLNV/Name)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:template>
	<!-- start of processing -->
	<xsl:template match="/">
		<xsl:apply-templates/>
	</xsl:template>
	<!-- default behavior: do not copy -->
	<xsl:template match="@*|node()">
		<xsl:apply-templates select="@*|node()"/>
	</xsl:template>
	<!-- Make the document -->
	<xsl:template match="SbfInstanceDefinition">
		<xsl:comment>====</xsl:comment>
		<xsl:comment>&#169; Copyright Infineon Technologies AG 2016. All rights reserved</xsl:comment>
		<xsl:comment>====</xsl:comment>
		<xsl:comment>Version of used XSLT processor: <xsl:value-of select="system-property('xsl:version')"/>
			<xsl:text> </xsl:text>
			<xsl:value-of select="system-property('xsl:vendor')"/>
			<xsl:text> </xsl:text>
			<xsl:value-of select="system-property('xsl:vendor-url')"/>
		</xsl:comment>
		<xsl:comment>
			<xsl:text>Version of used XSLT: Instance2db </xsl:text>
			<xsl:value-of select="$toolversion"/>
		</xsl:comment>
		<DB><!-- no namespace required -->
			<!-- insert Metadata table -->
			<MetaData audience="Internal">
				<S_Table frame="topbot" cols="3" colsep="1" rowsep="1" Type="Normal">
					<xsl:attribute name="cwidths" select="'1.263in 1.407in 4.230in'"/>
					<TableTitle>
						<TCaption>Document Level Metadata</TCaption>
					</TableTitle>
					<S_Head>
						<S_HRow rowsep="1">
							<S_HCell colname="1" hAlign="Normal">
								<S_HCellBody>Namespace</S_HCellBody>
							</S_HCell>
							<S_HCell colname="2" hAlign="Normal">
								<S_HCellBody>Property</S_HCellBody>
							</S_HCell>
							<S_HCell colname="3" hAlign="Normal">
								<S_HCellBody>Value</S_HCellBody>
							</S_HCell>
						</S_HRow>
					</S_Head>
					<S_Body>
						<S_Row rowsep="1">
							<S_Cell colname="1">
								<S_CellBody>dc</S_CellBody>
							</S_Cell>
							<S_Cell colname="2">
								<S_CellBody>Creator</S_CellBody>
							</S_Cell>
							<S_Cell colname="3">
								<S_CellBody>
									<UserVariable Name="Doc_Author">Doc_Author</UserVariable>
								</S_CellBody>
							</S_Cell>
						</S_Row>
						<S_Row rowsep="1">
							<S_Cell colname="1">
								<S_CellBody>dc</S_CellBody>
							</S_Cell>
							<S_Cell colname="2">
								<S_CellBody>Title</S_CellBody>
							</S_Cell>
							<S_Cell colname="3">
								<S_CellBody>Instance Sheet</S_CellBody>
							</S_Cell>
						</S_Row>
						<S_Row rowsep="1">
							<S_Cell colname="1">
								<S_CellBody>dc</S_CellBody>
							</S_Cell>
							<S_Cell colname="2">
								<S_CellBody>Description</S_CellBody>
							</S_Cell>
							<S_Cell colname="3">
								<S_CellBody>Instance specifications for silicon <xsl:value-of select="$effectiveFilter"/>
								</S_CellBody>
							</S_Cell>
						</S_Row>
						<S_Row rowsep="1">
							<S_Cell colname="1">
								<S_CellBody>xapBJ</S_CellBody>
							</S_Cell>
							<S_Cell colname="2">
								<S_CellBody>JobRef</S_CellBody>
							</S_Cell>
							<S_Cell colname="3">
								<S_CellBody>
									<xsl:value-of select="f:cleanFileName(base-uri())"/>
								</S_CellBody>
							</S_Cell>
						</S_Row>
						<xsl:if test="string-length($IProot) &gt; 1">
							<S_Row rowsep="1">
								<S_Cell colname="1">
									<S_CellBody>ifx</S_CellBody>
								</S_Cell>
								<S_Cell colname="2">
									<S_CellBody>Library</S_CellBody>
								</S_Cell>
								<S_Cell colname="3">
									<xsl:for-each select="tokenize($IProot,',')">
										<S_CellBody>
											<xsl:value-of select="f:cleanFileName(.)"/>
										</S_CellBody>
									</xsl:for-each>
								</S_Cell>
							</S_Row>
						</xsl:if>
						<xsl:for-each-group select="//Instance[not(./Silicon) or contains(string-join(('|',./Silicon/text(),'|'),'|'),concat('|',$effectiveFilter,'|'))]" group-by="VLNV/Name/text()">
							<xsl:sort select="current-grouping-key()"/>
							<xsl:variable name="file" select="f:resolvePath2(f:makeKey(current-group()[1]/VLNV),1)"/>
							<xsl:if test="doc-available($file)">
								<S_Row rowsep="1">
									<S_Cell colname="1">
										<S_CellBody>ifx</S_CellBody>
									</S_Cell>
									<S_Cell colname="2">
										<S_CellBody>Reference</S_CellBody>
									</S_Cell>
									<S_Cell colname="3">
										<S_CellBody>
											<xsl:value-of select="f:cleanFileName($file)"/>
										</S_CellBody>
									</S_Cell>
								</S_Row>
							</xsl:if>
						</xsl:for-each-group>
					</S_Body>
				</S_Table>
			</MetaData>
			<!-- Instance chapters -->
			<xsl:for-each select="//Instance[(not(./Silicon) or contains(string-join(('|',./Silicon/text(),'|'),'|'),concat('|',$effectiveFilter,'|'))) and ((@type,@xsi:type)='VirtualInstance' or (@type,@xsi:type)='ComponentInstance')]">
				<!-- top level components, Virtual components -->
				<xsl:sort select="(@type,@xsi:type)[1]"/>
				<xsl:sort select="concat(ConceptName,DesignName)"/>
				<xsl:variable name="self" select="Int_Class_ID"/>
				<xsl:variable name="shell">
					<xsl:variable name="ref" select="ComponentInstanceReference[not(./Silicon) or contains(string-join(('|',./Silicon/text(),'|'),'|'),concat('|',$effectiveFilter,'|'))]/ComponentInstanceRef"/>
					<xsl:if test="//Instance[Int_Class_ID = $ref]">
						<xsl:copy-of select="//Instance[Int_Class_ID = $ref]/ParameterMap"/>
					</xsl:if>
				</xsl:variable>
				<xsl:variable name="fileref" select="f:makeKey(VLNV)"/>
				<xsl:variable name="specname" select="f:specName(.)"/>
				<!-- Instance chapter -->
				<Instance>
					<xsl:copy-of select="@type|@xsi:type"/>
					<xsl:attribute name="InstanceName" select="f:specName(.)"/>
					<xsl:attribute name="Essence" select="$fileref"/>
					<xsl:for-each select="InstanceProperty[contains($extracolumns,concat('|',normalize-space(Name/text()),'|'))]">
						<xsl:attribute name="{Name/text()}" select="string(Value)"/>
					</xsl:for-each>			
					<!-- find sockets -->		
					<xsl:for-each select="$IPdefs/Interfaces[@key=$fileref]/Interface[ExtVLNV and not(AddressBlock)]">
						<xsl:variable name="file" select="f:resolvePath2(f:makeKey(ExtVLNV),1)"/>
						<xsl:if test="doc-available($file)">
							<xsl:variable name="myname" as="xs:string*"><!-- matchname,prefix -->
								<xsl:choose>
									<xsl:when test="ShortName and string-length(replace(ShortName,'^.*?:(.*?)&quot;?$',''))">
										<xsl:value-of select="translate(replace(ShortName,'^.*?:',''),'&quot;','')"/>
										<xsl:value-of select="concat(translate(replace(ShortName,'^.*?:',''),'&quot;',''),'_')"/>
									</xsl:when>
									<xsl:when test="string-length(normalize-space(Name))=0">
										<xsl:value-of select="lower-case(ExtVLNV/Name)"/>
									</xsl:when>
									<xsl:when test="normalize-space(Name)=lower-case(ExtVLNV/Name)">
										<xsl:value-of select="lower-case(ExtVLNV/Name)"/>
									</xsl:when>
									<xsl:otherwise>
										<xsl:value-of select="normalize-space(Name)"/>
										<xsl:value-of select="concat(normalize-space(Name),'_')"/>
									</xsl:otherwise>
								</xsl:choose>
							</xsl:variable>					
							<xsl:variable name="role" select="Role"/>
							<xsl:variable name="socket" select="document($file)"/>
							<xsl:choose>
								<xsl:when test="$socket//InterfaceDefRole[Role/text()=$role]">
									<xsl:apply-templates select="$socket//InterfaceDefRole[Role/text()=$role]">
										<xsl:with-param name="interface" select="$myname"/>
										<xsl:with-param name="reverse" select="0"/>
										<xsl:with-param name="excludes" select="./InterfaceView[Name='RTL' and not(f:toBoolean((IsConnected,'false')))]/InterfacePortMap[XRefLocalPort/XRefTargetID='0']/XRefInterfacePort/XRefTargetID"/>
										<xsl:with-param name="includes" select="./InterfaceView[Name='RTL' and f:toBoolean((IsConnected,'false'))]/InterfacePortMap[XRefLocalPort/XRefTargetID='0']/XRefInterfacePort/XRefTargetID"/>
									</xsl:apply-templates>
								</xsl:when>
								<xsl:when test="$socket//InterfaceDefRole[concat('Mirrored',Role/text())=$role]">
									<xsl:apply-templates select="$socket//InterfaceDefRole[concat('Mirrored',Role/text())=$role]">
										<xsl:with-param name="interface" select="$myname"/>
										<xsl:with-param name="reverse" select="1"/>
										<xsl:with-param name="excludes" select="./InterfaceView[Name='RTL' and not(f:toBoolean((IsConnected,'false')))]/InterfacePortMap[XRefLocalPort/XRefTargetID='0']/XRefInterfacePort/XRefTargetID"/>
										<xsl:with-param name="includes" select="./InterfaceView[Name='RTL' and f:toBoolean((IsConnected,'false'))]/InterfacePortMap[XRefLocalPort/XRefTargetID='0']/XRefInterfacePort/XRefTargetID"/>
									</xsl:apply-templates>
								</xsl:when>
								<xsl:when test="$socket//InterfaceDefRole[Role/text()=concat('Mirrored',$role)]">
									<xsl:apply-templates select="$socket//InterfaceDefRole[Role/text()=concat('Mirrored',$role)]">
										<xsl:with-param name="interface" select="$myname"/>
										<xsl:with-param name="reverse" select="1"/>
										<xsl:with-param name="excludes" select="./InterfaceView[Name='RTL' and not(f:toBoolean((IsConnected,'false')))]/InterfacePortMap[XRefLocalPort/XRefTargetID='0']/XRefInterfacePort/XRefTargetID"/>
										<xsl:with-param name="includes" select="./InterfaceView[Name='RTL' and f:toBoolean((IsConnected,'false'))]/InterfacePortMap[XRefLocalPort/XRefTargetID='0']/XRefInterfacePort/XRefTargetID"/>
									</xsl:apply-templates>
								</xsl:when>							
							</xsl:choose>
						</xsl:if>
					</xsl:for-each>
					<xsl:variable name="filters" as="item()*">
						<xsl:for-each select="./ParameterMap[$filterparams=Name/text()]">
							<xsl:variable name="pn" select="./Name/text()"/>
							<xsl:for-each select="tokenize(normalize-space(translate(./Value/text(),'&quot;','')),' ')">
								<Value>
									<xsl:attribute name="Name" select="$pn"/>
									<xsl:attribute name="Style" select="'Emphasis'"/>
									<xsl:value-of select="."/>
								</Value>
							</xsl:for-each>
						</xsl:for-each>
						<xsl:for-each select="$shell/ParameterMap[$filterparams=Name/text()]">
							<xsl:variable name="pn" select="./Name/text()"/>
							<xsl:for-each select="tokenize(normalize-space(translate(./Value/text(),'&quot;','')),' ')">
								<Value>
									<xsl:attribute name="Name" select="$pn"/>
									<xsl:attribute name="Style" select="'Normal'"/>
									<xsl:value-of select="."/>
								</Value>
							</xsl:for-each>
						</xsl:for-each>
						<xsl:for-each select="$DefaultFilters[$filterparams=Name/text()]">
							<xsl:variable name="pn" select="./Name/text()"/>
							<xsl:for-each select="tokenize(normalize-space(translate(./Value/text(),'&quot;','')),' ')">
								<InitialValue>
									<xsl:attribute name="Name" select="$pn"/>
									<xsl:attribute name="Style" select="'Designation'"/>
									<xsl:value-of select="."/>
								</InitialValue>
							</xsl:for-each>
						</xsl:for-each>
						<xsl:for-each select="$IPdefs/Parameters[@key=$fileref]/ParamDecl[$filterparams=Name/text()]">
							<xsl:variable name="pn" select="./Name/text()"/>
							<xsl:for-each select="tokenize(normalize-space(translate(./DefaultValue/text(),'&quot;','')),' ')">
								<DefaultValue>
									<xsl:attribute name="Name" select="$pn"/>
									<xsl:attribute name="Style" select="'Designation'"/>
									<xsl:value-of select="."/>
								</DefaultValue>
							</xsl:for-each>
						</xsl:for-each>
					</xsl:variable>
					<!-- Instance filter table -->
					<xsl:for-each-group select="$filters" group-by="@Name">
						<xsl:sort select="current-grouping-key()"/>
						<xsl:if test="current-group()[local-name()='DefaultValue']">
							<xsl:variable name="haveInit" select="count(current-group()[local-name()='InitialValue'])"/>
							<Parameter>
								<xsl:attribute name="Name" select="current-grouping-key()"/>
								<xsl:attribute name="Type" select="'FILTER'"/>
								<xsl:variable name="haveSpec" as="xs:integer*">
									<xsl:for-each-group select="current-group()" group-by="text()">
										<xsl:if test="current-group()[local-name()='DefaultValue']">
											<xsl:value-of select="count(current-group()[@Style!='Designation'])"/>
										</xsl:if>
									</xsl:for-each-group>
								</xsl:variable>
								<xsl:for-each-group select="current-group()" group-by="text()">
									<xsl:sort select="current-grouping-key()"/>
									<xsl:choose>
										<xsl:when test="not(current-group()[local-name()='DefaultValue'])"/>
										<!-- skip values not defined in the component -->
										<xsl:when test="current-group()[local-name()='Value']">
											<!-- take the most locally defined mapping value instance or shell -->
											<ph>
												<xsl:copy-of select="current-group()[local-name()='Value'][1]/@Style"/>
												<xsl:value-of select="current-grouping-key()"/>
											</ph>
										</xsl:when>
										<xsl:when test="current-group()[local-name()='InitialValue']">
											<!-- take the mapping value from the common sheet -->
											<ph>
												<xsl:copy-of select="current-group()[local-name()='InitialValue'][1]/@Style"/>
												<xsl:value-of select="current-grouping-key()"/>
											</ph>
										</xsl:when>
										<xsl:when test="$haveInit &gt; 0"/>
										<!-- skip defaults when there is any mapping on the common sheet -->
										<xsl:when test="count($haveSpec[. &gt; 0]) &gt; 0"/>
										<xsl:otherwise>
											<ph>
												<xsl:copy-of select="current-group()[local-name()!='Value'][1]/@Style"/>
												<xsl:value-of select="current-grouping-key()"/>
											</ph>
										</xsl:otherwise>
									</xsl:choose>
								</xsl:for-each-group>
							</Parameter>
						</xsl:if>
					</xsl:for-each-group>
					<xsl:variable name="addrs">
						<xsl:for-each select="BusInstanceReference/BusInterfaceMap">
							<xsl:choose>
								<xsl:when test="(@type,@xsi:type)='BusSlaveInterfaceMap'">
									<ParameterMap>
										<Name>
											<xsl:value-of select="concat(Interface,'_base')"/>
										</Name>
										<Type>INTEGER</Type>
										<Value>
											<xsl:value-of select="StartAddress"/>
										</Value>
									</ParameterMap>
									<ParameterMap>
										<Name>
											<xsl:value-of select="concat(Interface,'_range')"/>
										</Name>
										<Type>INTEGER</Type>
										<Value>0x<xsl:value-of select="f:decimal-to-hex(f:integerEssence(EndAddress/text()) - f:integerEssence(StartAddress/text()) + 1)"/>
										</Value>
									</ParameterMap>
								</xsl:when>
								<xsl:when test="(@type,@xsi:type)='BusMasterInterfaceMap' and StartAddress">
									<xsl:variable name="targetAdr" select="StartAddress/text()"/>
									<xsl:variable name="myname" select="Interface/text()"/>
									<!-- the target offset is given in Mapping for the Master role but must be named with the associated Slave role -->
									<xsl:variable name="masterID" as="xs:string*">
										<!-- get ID of master interface -->
										<xsl:for-each select="$IPdefs/Interfaces[@key=$fileref]/Interface[Role = 'Master' and f:booleanEssence(Hidden,$self) = 0]">
											<xsl:variable name="design">
												<xsl:call-template name="guessName"/>
											</xsl:variable>
											<xsl:if test="$design = $myname">
												<xsl:value-of select="ID"/>
											</xsl:if>
										</xsl:for-each>
										<xsl:value-of select="'unknown'"/>
										<!-- ECB file inconsistent or buggy -->
									</xsl:variable>
									<xsl:for-each select="$IPdefs/Interfaces[@key=$fileref]/Interface[AddressBlock/XRefMasterInterface/XRefTargetID = $masterID[1]]">
										<!-- find slave interfaces -->
										<ParameterMap>
											<xsl:variable name="design">
												<xsl:call-template name="guessName"/>
											</xsl:variable>
											<Name>
												<xsl:value-of select="concat($design,'_dest')"/>
											</Name>
											<Type>INTEGER</Type>
											<Value>
												<xsl:value-of select="$targetAdr"/>
											</Value>
										</ParameterMap>
									</xsl:for-each>
								</xsl:when>
							</xsl:choose>
						</xsl:for-each>
					</xsl:variable>
					<xsl:variable name="vars">
						<xsl:copy-of select="./ParameterMap[not($filterparams=Name/text())]"/>
						<xsl:copy-of select="$addrs/*"/>
					</xsl:variable>
					<xsl:variable name="lines">
						<xsl:if test="$vars">
							<xsl:for-each-group select="$vars/*" group-by="*[local-name()='Name']/text()">
								<xsl:for-each select="current-group()[1]">
									<Row>
										<Name>
											<xsl:value-of select="current-grouping-key()"/>
										</Name>
										<Type>
											<xsl:value-of select="*[local-name()='Type']/text()"/>
										</Type>
										<Value>
											<ph Type="Explicit">
												<xsl:value-of select="*[local-name()='Value']/text()"/>
											</ph>
										</Value>
									</Row>
								</xsl:for-each>
							</xsl:for-each-group>
						</xsl:if>
						<xsl:if test="$IPdefs/Parameters[@key=$fileref]">
							<xsl:for-each select="$IPdefs/Parameters[@key=$fileref]/ParamDecl[not($filterparams=Name/text())]">
								<xsl:variable name="pn" select="Name/text()"/>
								<xsl:if test="not($vars) or not($vars//*[local-name()='Name' and text() = $pn])">
									<Row>
										<Name>
											<xsl:value-of select="$pn"/>
										</Name>
										<xsl:if test="Property[Key/text()='Hidden']">
											<Hidden>
												<xsl:value-of select="Property[Key/text()='Hidden']/Value/text()"/>
											</Hidden>
										</xsl:if>
										<Type>
											<xsl:value-of select="upper-case(substring-before(@xsi:type,'Decl'))"/>
										</Type>
										<Value>
											<xsl:choose>
												<xsl:when test="$shell and $shell/ParameterMap[Name/text() = $pn]">
													<ph Type="Inherit">
														<xsl:value-of select="$shell/ParameterMap[Name/text() = $pn]/Value"/>
													</ph>
												</xsl:when>
												<xsl:when test="$Commons//*[local-name() = 'Name' and text() = $pn]">
													<ph Type="Inherit">
														<xsl:value-of select="$Commons//*[local-name() = 'Name' and text() = $pn]/../*[local-name()='Value']"/>
													</ph>
												</xsl:when>
												<xsl:otherwise>
													<ph Type="Default">
														<xsl:value-of select="DefaultValue/text()"/>
													</ph>
												</xsl:otherwise>
											</xsl:choose>
										</Value>
									</Row>
								</xsl:if>
							</xsl:for-each>
						</xsl:if>
					</xsl:variable>
					<!-- Instance parameter table -->
					<xsl:for-each select="$lines/Row">
						<xsl:sort select="Name"/>
						<Parameter>
							<xsl:attribute name="Name" select="Name/*|Name/text()"/>
							<xsl:if test="Hidden"><xsl:attribute name="Hidden" select="Hidden/text()"/></xsl:if>
							<xsl:attribute name="Type" select="Type/*|Type/text()"/>
							<xsl:copy-of select="Value/*|Value/text()"/>
						</Parameter>
					</xsl:for-each>
					<xsl:variable name="gens" select="./GenericMap"/>
					<xsl:variable name="glines">
						<xsl:if test="$gens">
							<xsl:for-each select="$gens">
								<xsl:variable name="pn" select="Name/text()"/>
								<Row>
									<Name>
										<xsl:value-of select="$pn"/>
									</Name>
									<Type>
										<xsl:value-of select="Type/text()"/>
									</Type>
									<Value>
										<ph Type="Explicit">
											<xsl:value-of select="Value/text()"/>
										</ph>
									</Value>
								</Row>
							</xsl:for-each>
						</xsl:if>
						<xsl:if test="$IPdefs/Parameters[@key=$fileref]">
							<xsl:for-each select="$IPdefs/Parameters[@key=$fileref]/GenericDecl">
								<xsl:variable name="pn" select="Name/text()"/>
								<xsl:if test="not($gens) or not($gens[Name/text() = $pn])">
									<Row>
										<Name>
											<xsl:value-of select="$pn"/>
										</Name>
										<Type>
											<xsl:value-of select="upper-case(substring-before(@xsi:type,'GenDecl'))"/>
										</Type>
										<Value>
											<xsl:choose>
												<xsl:when test="$shell and $shell/GenericMap[Name/text() = $pn]">
													<ph Type="Inherit">
														<xsl:value-of select="$shell/GenericMap[Name/text() = $pn]/Value"/>
													</ph>
												</xsl:when>
												<xsl:when test="$Commons//*[local-name() = 'Name' and text() = $pn]">
													<ph Type="Inherit">
														<xsl:value-of select="$Commons//*[local-name() = 'Name' and text() = $pn]/../*[local-name()='Value']"/>
													</ph>
												</xsl:when>
												<xsl:otherwise>
													<ph Type="Default">
														<xsl:value-of select="DefaultValue/text()"/>
													</ph>
												</xsl:otherwise>
											</xsl:choose>
										</Value>
									</Row>
								</xsl:if>
							</xsl:for-each>
						</xsl:if>
					</xsl:variable>
					<!-- Instance generics table -->
					<xsl:for-each select="$glines/Row">
						<xsl:sort select="Name/text()"/>
						<Parameter>
							<xsl:attribute name="Name" select="Name/*|Name/text()"/>
							<xsl:attribute name="Type" select="Type/*|Type/text()"/>
							<xsl:copy-of select="Value/*|Value/text()"/>
						</Parameter>
					</xsl:for-each>
				</Instance>
			</xsl:for-each>
		</DB>
	</xsl:template>
	<!--=====================================-->
	<xsl:template match="InterfaceDefRole">
		<xsl:param name="interface" as="xs:string*"/>
		<xsl:param name="reverse" select="0"/>
		<xsl:param name="excludes" as="item()*"/>
		<xsl:param name="includes" as="item()*"/>
		<Socket Name="{$interface[1]}">			
			<xsl:variable name="socketPrefix" select="$interface[2]"/>
			<xsl:for-each select="./InterfaceDefPort">
				<xsl:variable name="id" select="ID"/>
				<xsl:variable name="signal" select="../../Signal[ID/text()=current()/XRefSignal/XRefTargetID/text()]"/>
				<xsl:choose>
					<xsl:when test="$excludes[text()=$id]">
						<xsl:if test="Property[Key='owner']/Value='concept' or $signal/Property[Key='owner']/Value='concept'">
							<xsl:comment>excluding <xsl:value-of select="$signal/ID/text()"/></xsl:comment>
						</xsl:if>
					</xsl:when>
					<xsl:when test="count($includes) and count($includes[text()=$id])=0">
						<xsl:if test="Property[Key='owner']/Value='concept' or $signal/Property[Key='owner']/Value='concept'">
							<xsl:comment>not including <xsl:value-of select="$signal/ID/text()"/></xsl:comment>
						</xsl:if>
					</xsl:when>
					<xsl:when test="Property[Key='owner']/Value and Property[Key='owner']/Value!='concept'"/>
					<xsl:when test="not($signal/Property[Key='owner']/Value) or $signal/Property[Key='owner']/Value!='concept'"/>
					<xsl:otherwise>									
						<Member>
							<xsl:attribute name="wire" select="$signal/ID/text()"/>
							<xsl:variable name="myName" as="xs:string*">
								<xsl:choose>
									<xsl:when test="ShortName and string-length(ShortName)">
										<xsl:value-of select="translate(ShortName,'&quot;','')"/>
									</xsl:when>
									<xsl:when test="$signal/ShortName and string-length($signal/ShortName)">
										<xsl:value-of select="translate($signal/ShortName,'&quot;','')"/>
									</xsl:when>
									<xsl:otherwise>
										<xsl:value-of select="normalize-space(replace(Name,'^(.*?)_a?[io]\s*$','$1'))"/>
									</xsl:otherwise>
								</xsl:choose>
							</xsl:variable>					
							<xsl:value-of select="concat($socketPrefix,$myName)"/>
							<xsl:if test="$signal/DataType/Vector">
								<xsl:copy-of select="$signal/DataType/Vector" copy-namespaces="no"/>
							</xsl:if>
							<xsl:choose>
								<xsl:when test="$reverse=1 and ./Direction='in'"><Direction>out</Direction></xsl:when>
								<xsl:when test="$reverse=1 and ./Direction='out'"><Direction>in</Direction></xsl:when>
								<xsl:otherwise><xsl:copy-of select="./Direction" copy-namespaces="no"/></xsl:otherwise>
							</xsl:choose>	
						</Member>											
					</xsl:otherwise>
				</xsl:choose>								
			</xsl:for-each>
		</Socket>
	</xsl:template>
	<!--=====================================-->
	<xsl:function name="f:specName" as="xs:string">
		<xsl:param name="inst"/>
		<xsl:choose>
			<xsl:when test="$inst/ConceptName">
				<xsl:value-of select="$inst/ConceptName"/>
			</xsl:when>
			<xsl:when test="not($inst/DesignName)">
				<xsl:value-of select="$inst/VLNV/Name"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$inst/DesignName"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	
	<xsl:function name="f:toBoolean" as="xs:boolean">
		<xsl:param name="in" as="xs:string*"/>
		<xsl:choose>
			<xsl:when test="count($in)!=0 and matches($in[1],'TRUE','i')"><xsl:value-of select="true()"/></xsl:when>
			<xsl:otherwise><xsl:value-of select="false()"/></xsl:otherwise>
		</xsl:choose>
	</xsl:function>
</xsl:stylesheet>
