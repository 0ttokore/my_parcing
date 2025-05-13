<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fn="http://www.w3.org/2005/xpath-functions" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xpath-default-namespace="http://www.duolog.com/socrates/5PBuilder/2012/01" xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009" xmlns:ifx="http://www.infineon.com/cms/xml/SPIRIT_IO_1685/1.0/EN" xmlns:f="http://www.infineon.com" exclude-result-prefixes="f fn xs">
	<!--	================================================================================	-->
	<!-- Started by IFAG BEX RDE DOC, Harry Siebert 2013  -->
	<!-- Infineon Technologies AG, Documentation Methodologies	 -->
	<!--	-->
	<!--	This XSLT transforms a SOC specification from SBF to Spirit -->
	<!--	-->
	<xsl:param name="toolversion" select="'2.1'"/>
	<!--	Version History:	-->
	<!--	V2.1	Constraints added to resource instances	-->
	<!--	V2.0	A2G first draft	-->
	<!--	V1.*	AURIX	-->
	<!--	-->
	<xsl:param name="debug" select="'0'"/>
	<!-- ======================================================================= -->
	<!-- Command line parameters -->
	<xsl:param name="family" select="'AURIXTC3XX'"/>
	<!-- family name as on coversheet -->
	<xsl:param name="label" select="1"/>
	<!-- clearcase label -->
	<xsl:param name="Package" select="'BGA516'"/>
	<!-- file name component for database files -->
	<xsl:param name="Device" select="'TC39x'"/>
	<!-- the version of the silicon -->
	<xsl:param name="silicon_step" select="'A'"/>
 	<!-- Spirit Bill of Material -->
	<xsl:param name="BOM" select="'TC39x_LFBGA516_bom.xml'"/>
	<!-- dump of the connexion database -->
	<xsl:param name="Connections" select="'//ccm.vih.infineon.com/rmrepo/pool1/config/Arch_Spec_TC39x/V2.0.0.1.1/conn_spec/lnk/TC39X.xml'"/>
	<!-- file name component for mapping files -->
	<xsl:param name="IProot" select="''"/>
	<!-- file name component for patch files -->
	<!-- xsl:param name="PatchRoot" select="'///C:/Users/siebert/siebert_AurixPlus_20141216_073749_snp/MC_Specs/Modules/GTM_AURIXPLUS/GTM_IFX/topics/'"/ -->
	<xsl:param name="PatchRoot" select="''"/>
	<!-- ======================================================================= -->
	<!-- reusable stuff -->
	<xsl:include href="./mathlib2.xslt"/>
	<xsl:function name="f:calcFormulas" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:variable name="evaluated">
			<xsl:analyze-string select="$input" regex="\{{.*?\}}" flags="s">
				<xsl:matching-substring>
					<xsl:value-of select="f:evaluate(normalize-space(substring(.,2,string-length(.)-2)))"/>
				</xsl:matching-substring>
				<xsl:non-matching-substring>
					<xsl:value-of select="." disable-output-escaping="yes"/>
				</xsl:non-matching-substring>
			</xsl:analyze-string>
		</xsl:variable>
		<xsl:value-of select="string-join($evaluated,'')"/>
	</xsl:function>
	<xsl:function name="f:enumerate" as="xs:string*">
		<xsl:param name="range" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:for-each select="tokenize($range,',')">
			<xsl:variable name="toks" select="tokenize(.,':')"/>
			<xsl:choose>
				<xsl:when test="count($toks) &gt; 2">
					<xsl:message terminate="yes">Illegal range spec "<xsl:value-of select="$range"/>" in <xsl:value-of select="$context"/></xsl:message>
				</xsl:when>
				<xsl:when test="count($toks) &lt; 2">
					<xsl:value-of select="f:evaluate($toks[1])"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:variable name="end" select="xs:integer(f:evaluate($toks[1]))"/>
					<xsl:variable name="start" select="xs:integer(f:evaluate($toks[2]))"/>
					<xsl:choose>
						<xsl:when test="$start &lt; $end">
							<xsl:for-each select="for $i in $start to $end return $i">
								<xsl:value-of select="xs:string(.)"/>
							</xsl:for-each>
						</xsl:when>
						<xsl:otherwise>
							<xsl:for-each select="for $i in $end to $start return $i">
								<xsl:value-of select="xs:string(.)"/>
							</xsl:for-each>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:otherwise>
			</xsl:choose>		
		</xsl:for-each>
	</xsl:function>
	<!-- ======================================================================= -->
	<!-- list of all functional pads -->
	<xsl:variable name="PINS" select="//spinner5PBuilder/ioPad[(matches(@name,'^P\d+_\d+$') or matches(@name,'^AN\d+$') or 
										matches(@name,'(PORST|ESR\d|TRST|TCK|TMS|DAPE\d|CLK_\D|ERR_SIG|TX_\D|CTRL\dV\d\D|XTAL\d)$')) 
									and (not(properties/Address[@package=$Package]) or not(starts-with(properties/Address[@package=$Package],'(')))]/@name"/>
	<xsl:function name="f:locatePin">
		<!-- get the instance name for a given pad name -->
		<xsl:param name="name" as="xs:string"/>
		<xsl:variable name="inst">
			<xsl:for-each select="$PINS">
				<xsl:if test=". = translate($name,'.','_')">
					<xsl:choose>
						<xsl:when test="matches($name,'^P\d+(_|\.)\d+$')">
							<xsl:value-of select="concat('PIN_',string(position()))"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="concat('DEDICATED_',string(position()))"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:if>
			</xsl:for-each>
		</xsl:variable>
		<xsl:value-of select="string-join(($inst),'')"/>
	</xsl:function>
	<!-- ======================================================================= -->
	<!-- database trees -->
	<xsl:key name="parameter" match="/*/*" use="concat(../@Int_Class_ID,':',@Name)"/>
	<!-- $ParaMaps2/key('parameter',concat($context,':',$Name) -->
	<xsl:key name="filter" match="/*/*" use="concat(../@Int_Class_ID,':',@Name)"/>
	<!-- $ParaMaps2/key('filter',concat($context,':',$Name) -->
	<xsl:key name="instance" match="/*" use="string(@Int_Class_ID)"/>
	<!-- $ParaMaps2/key('instance',$context) -->
	<xsl:variable name="ParaMaps2">
		<xsl:if test="doc-available($BOM)">
			<!-- get instances from the instance sheet -->
			<xsl:copy-of select="document($BOM)/*/*"/>
			<!-- get map files -->
			<xsl:for-each-group select="document($BOM)/*/*" group-by="local-name()">
				<xsl:variable name="module" select="current-grouping-key()"/>
				<xsl:variable name="file" select="concat($IProot,current-grouping-key(),'.xml')"/>
				<xsl:if test="doc-available($file)">
					<xsl:for-each select="document($file)/*">
						<xsl:element name="{concat(@IP,'spec')}">
							<xsl:copy-of select="@*[local-name()!='IP']"/>
							<xsl:copy-of select="*[not(local-name()='Mux' or local-name()='IMux' or local-name()='INet')]"/>
							<xsl:variable name="aliases" select="*[*[local-name()='ConceptInstanceName' and text()='@']]"/>
							<!-- get patch files -->
							<xsl:for-each-group select="*[local-name()='Mux' or local-name()='IMux' or local-name()='INet']" group-by="@File">
								<xsl:for-each select="tokenize($PatchRoot,',')">
									<xsl:variable name="file" select="concat(.,current-grouping-key())"/>
									<xsl:if test="unparsed-text-available($file)">
										<xsl:message terminate="no">Importing input mappings from <xsl:value-of select="$file"/></xsl:message>
										<xsl:variable name="excel" select="f:readExcelCSV($file)"/><!-- array of <row> -->
										<xsl:variable name="blocks" select="f:tokenizeExcel($excel)"/><!-- array of <header> -->
										<xsl:variable name="bitfields" as="item()*"><!-- array of <Bitfield> -->
											<xsl:for-each select="$blocks">
												<xsl:variable name="head" select="."/>
												<xsl:variable name="i" select="position()"/>
												<xsl:variable name="ends" select="if ($i=last()) then $excel[last()]/@n+1 else $blocks[position()=$i+1]/@start"/>										
												<xsl:for-each select="$excel[number(@n) &gt; number($head/@start) and number(@n) &lt; number($ends) and string-length(*[local-name()='col' and position()=$head/@Bitfield])]">
													<Bitfield>
														<xsl:copy-of select="$head/@*"/>
														<xsl:attribute name="start" select="@n"/>
														<xsl:attribute name="ends" select="$ends"/><!-- end of block -->
														<xsl:attribute name="Shortname" select="*[local-name()='col' and position()=$head/@Bitfield]"/>
														<xsl:if test="string-length(*[local-name()='col' and position()=$head/@Filter])">
															<Filter><xsl:value-of select="*[local-name()='col' and position()=$head/@Filter]"/></Filter>
														</xsl:if>
														<xsl:variable name="varmap" as="item()*">
															<xsl:for-each select="tokenize(translate(string-join((*[local-name()='col' and position() &gt;= number($head/@Indices)]),';'),'&quot;',''),';')">
																<xsl:if test="contains(.,'=')">
																	<index>
																		<xsl:attribute name="Name" select="normalize-space(substring-before(.,'='))"/>
																		<xsl:value-of select="substring-after(.,'=')"/>
																	</index>
																</xsl:if>
															</xsl:for-each>
														</xsl:variable>
														<xsl:if test="count($varmap)">
															<varmap>
																<xsl:copy-of select="$varmap"/>
															</varmap>
														</xsl:if>
													</Bitfield>
												</xsl:for-each>										
											</xsl:for-each>
										</xsl:variable>
										<xsl:for-each select="current-group()">
											<xsl:variable name="mux" select="."/>
											<xsl:for-each select="$bitfields">
												<xsl:if test="matches(@Shortname,$mux/@Name)">
													<xsl:variable name="bitfield" select="."/>
													<xsl:variable name="j" select="position()"/>
													<xsl:variable name="rends" select="if ($j=last()) then @ends else $bitfields[position()=$j+1]/@start"/>
													<xsl:for-each select="$excel[number(@n) &gt; number($bitfield/@start) and number(@n) &lt; number($rends)]">
														<xsl:variable name="rawname" as="xs:string">
															<xsl:variable name="altName">
																<xsl:choose>
																	<xsl:when test="$bitfield/@AltSymbol">
																		<xsl:value-of select="normalize-space(translate(*[local-name()='col' and position()=$bitfield/@AltSymbol],'&quot;',''))"/>
																	</xsl:when>
																	<xsl:otherwise><xsl:value-of select="''"/></xsl:otherwise>
																</xsl:choose>
															</xsl:variable>
															<xsl:choose>
																<xsl:when test="string-length($altName) = 0">
																	<xsl:value-of select="normalize-space(replace(translate(*[local-name()='col' and position()=$bitfield/@Symbol],'&quot;)(',''),',.*$',''))"/>
																</xsl:when>
																<xsl:otherwise><xsl:value-of select="$altName"/></xsl:otherwise>
															</xsl:choose>
														</xsl:variable>
														<xsl:choose>
															<xsl:when test="string-length($rawname) = 0"/>
															<xsl:when test="string-length(*[local-name()='col' and position()=number($bitfield/@Value)]) = 0"/>
															<xsl:when test="local-name($mux)='INet'">
																<Net>
																	<xsl:for-each select="$bitfield/*[local-name()='varmap']/*">
																		<xsl:attribute name="{./@Name}" select="./text()"/>
																	</xsl:for-each>
																	<xsl:if test="string-length($excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Value)]/text()) &gt; 0">
																		<xsl:attribute name="{$excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Value)]}" select="*[local-name()='col' and position()=$bitfield/@Value]"/>
																	</xsl:if>
																	<xsl:if test="string-length($excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Symbol)]/text()) &gt; 0">
																		<xsl:attribute name="{$excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Symbol)]}" select="replace(*[local-name()='col' and position()=$bitfield/@Symbol],'[^\d]+','')"/>
																	</xsl:if>
																	<xsl:copy-of select="$mux/@Hidden|$mux/*"/>
																</Net>
															</xsl:when>
															<xsl:when test="local-name($mux)='IMux'">
																<Net>
																	<xsl:for-each select="$bitfield/*[local-name()='varmap']/*">
																		<xsl:attribute name="{./@Name}" select="./text()"/>
																	</xsl:for-each>
																	<xsl:if test="string-length($excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Value)]/text()) &gt; 0">
																		<xsl:attribute name="{$excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Value)]}" select="*[local-name()='col' and position()=$bitfield/@Value]"/>
																	</xsl:if>
																	<xsl:copy-of select="$mux/@Hidden"/>
																	<in>
																		<xsl:copy-of select="$mux/*"/>
																	</in>
																	<out>															
																		<ConceptInstanceName><xsl:value-of select="$module"/></ConceptInstanceName>
																		<ConceptName><xsl:value-of select="$rawname"/></ConceptName>
																	</out>
																</Net>
															</xsl:when>
															<xsl:when test="count($aliases[matches($rawname,@Name)])">
																<xsl:variable name="me" select="."/>
																<xsl:for-each select="$aliases[matches($rawname,@Name)]">
																	<Map>
																		<xsl:for-each select="$bitfield/*[local-name()='varmap']/*">
																			<xsl:attribute name="{./@Name}" select="./text()"/>
																		</xsl:for-each>
																		<xsl:if test="string-length($excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Value)]/text()) &gt; 0">
																			<xsl:attribute name="{$excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Value)]}" select="$me/*[local-name()='col' and position()=$bitfield/@Value]"/>
																		</xsl:if>
																		<xsl:copy-of select="@*[local-name()!='Name']"/>
																		<xsl:attribute name="Name" select="concat('^',replace($rawname,@Name,*[local-name()='ConceptName']/text()),'$')"/>
																		<xsl:copy-of select="$mux/*"/>
																	</Map>
																</xsl:for-each>
															</xsl:when>
															<xsl:otherwise>
																<Map>
																	<xsl:for-each select="$bitfield/*[local-name()='varmap']/*">
																		<xsl:attribute name="{./@Name}" select="./text()"/>
																	</xsl:for-each>
																	<xsl:if test="string-length($excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Value)]/text()) &gt; 0">
																		<xsl:attribute name="{$excel[number(@n) = number($bitfield/@start)]/*[local-name()='col' and position()=number($bitfield/@Value)]}" select="*[local-name()='col' and position()=$bitfield/@Value]"/>
																	</xsl:if>
																	<xsl:attribute name="Name" select="concat('^',$rawname,'$')"/>
																	<xsl:copy-of select="$mux/*"/>
																</Map>
															</xsl:otherwise>
														</xsl:choose>
													</xsl:for-each>
												</xsl:if>
											</xsl:for-each>
										</xsl:for-each>
									</xsl:if>
								</xsl:for-each>
							</xsl:for-each-group>
						</xsl:element>
					</xsl:for-each>
				</xsl:if>
			</xsl:for-each-group>
		</xsl:if>
		<!-- get default map files -->
		<xsl:for-each select="('PIN','DEDICATED')">
			<xsl:variable name="file" select="concat($IProot,.,'.xml')"/>
			<xsl:if test="doc-available($file)">
					<xsl:for-each select="document($file)/*">
						<xsl:element name="{concat(@IP,'spec')}">
							<xsl:copy-of select="@*[local-name()!='IP']"/>
							<xsl:copy-of select="*"/>
						</xsl:element>
					</xsl:for-each>
			</xsl:if>
		</xsl:for-each>
		<!-- synthesize pin instances -->
		<xsl:for-each select="$PINS">
			<xsl:variable name="trial" select="f:locatePin(.)"/>
			<xsl:element name="{substring-before($trial,'_')}">
				<xsl:attribute name="Int_Class_ID" select="$trial"/>
				<ParamDecl Name="inst"><Value><xsl:value-of select="substring-after($trial,'_')"/></Value></ParamDecl>
			</xsl:element>
		</xsl:for-each>
	</xsl:variable> 
	<!-- connection lists -->
	<!--			-->
	<!-- result: Array of pair elements with
          @ci = ConceptInstance  
          @cn = [ [ member ][ '[' [ highindex ':' ] lowindex ']' ]] '=' ] [ socket '.' ] ConceptName [ '[' [ highindex ':' ] lowindex ']' ]
    -->
	<xsl:function name="f:normalizeConceptNames" as="item()*">
		<xsl:param name="ci" as="xs:string"/>
		<xsl:param name="cn" as="xs:string"/>
		<xsl:choose>
			<xsl:when test="contains($ci,'|')"><!-- Legacy COX format -->
				<xsl:for-each select="tokenize($ci,'\|')">
					<xsl:choose>
						<xsl:when test="contains(.,':')"><pair ci="{substring-before(.,':')}" cn="{substring-after(.,':')}"/></xsl:when>
						<xsl:otherwise><xsl:copy-of select="f:normalizeConceptNames(.,$cn)"/></xsl:otherwise>
					</xsl:choose>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="contains($cn,'=(')"><!-- socket member is array -->
				<xsl:choose>
					<xsl:when test="contains($cn,';') and string-length(substring-before($cn,';')) &lt; string-length(substring-before($cn,'=('))">
						<xsl:copy-of select="f:normalizeConceptNames($ci,substring-before($cn,';'))"/>
						<xsl:copy-of select="f:normalizeConceptNames($ci,substring-after($cn,';'))"/>
					</xsl:when>
					<xsl:when test="contains(substring-after($cn,')'),';')">
						<xsl:copy-of select="f:normalizeConceptNames($ci,replace($cn,'\).*$',')'))"/>
						<xsl:copy-of select="f:normalizeConceptNames($ci,replace($cn,'^.*\)\s*;',''))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:variable name="member" select="substring-before($cn,'=(')"/>
						<xsl:for-each select="tokenize(replace($cn,'^.+?=\((.*)\)$','$1'),';')">
							<xsl:for-each select="f:normalizeConceptNames($ci,.)">
								<xsl:choose>
									<xsl:when test="contains(@cn,'=')"><pair ci="{@ci}" cn="{concat($member,'[',replace(@cn,'=',']='))}"/></xsl:when>
									<xsl:otherwise><pair ci="{@ci}" cn="{concat($member,'=',@cn)}"/></xsl:otherwise>
								</xsl:choose>					
							</xsl:for-each>
						</xsl:for-each>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="contains($cn,';')"><!-- members -->
				<xsl:copy-of select="f:normalizeConceptNames($ci,substring-before($cn,';'))"/>
				<xsl:copy-of select="f:normalizeConceptNames($ci,substring-after($cn,';'))"/>
			</xsl:when>
			<xsl:when test="contains($cn,'=')"><!-- array -->
				<xsl:variable name="range" select="substring-before($cn,'=')"/>
				<xsl:for-each select="f:normalizeConceptNames($ci,substring-after($cn,'='))">
					<pair ci="{@ci}" cn="{concat($range,'=',@cn)}"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="contains($cn,'|')"><!-- alias -->
				<xsl:for-each select="tokenize($cn,'\|')">
					<xsl:choose>
						<xsl:when test="contains(.,':')"><pair ci="{substring-before(.,':')}" cn="{substring-after(.,':')}"/></xsl:when>
						<xsl:otherwise><pair ci="{$ci}" cn="{.}"/></xsl:otherwise>
					</xsl:choose>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="contains($ci,':')"><pair ci="{substring-before($ci,':')}" cn="{substring-after($ci,':')}"/></xsl:when><!-- Legacy COX format -->
			<xsl:when test="contains($cn,':')"><pair ci="{substring-before($cn,':')}" cn="{substring-after($cn,':')}"/></xsl:when><!-- ignore COX CI -->
			<xsl:otherwise><pair ci="{$ci}" cn="{$cn}"/></xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:variable name="Connects" as="item()*">
		<xsl:variable name="connex" select="document($Connections)"/>
		<xsl:variable name="ports" as="item()*">
			<xsl:for-each select="$connex/*/*/*[local-name()='InterfaceItem' and *[local-name()='Type']/text()='PORT']">
				<port>
					<xsl:attribute name="ID" select="*[local-name()='Int_Class_ID']/text()"/>
					<xsl:copy-of select="*[local-name()='IsDriver' or local-name()='ConceptInstanceName' or local-name()='ConceptName' or local-name()='Name']"/>
				</port>
			</xsl:for-each>
		</xsl:variable>
		<xsl:variable name="sockets" as="item()*">
			<xsl:for-each select="$connex/*/*/*[local-name()='InterfaceItem' and *[local-name()='Type']/text()='INTERFACE']">
				<socket>
					<xsl:attribute name="ID" select="*[local-name()='Int_Class_ID']/text()"/>
					<xsl:copy-of select="*[local-name()='ConceptInstanceName' or local-name()='ConceptName' or local-name()='Name']"/>
					<xsl:element name="IsDriver">False</xsl:element>
				</socket>
			</xsl:for-each>
		</xsl:variable>
		<xsl:for-each select="$connex/*/*[local-name()='ConnectivityItem']">
			<xsl:variable name="nets" as="item()*">
				<xsl:for-each select="*[local-name()='InterfaceItemRef']">
					<xsl:copy-of select="$ports[@ID=current()/text()]"/>
					<xsl:copy-of select="$sockets[@ID=current()/text()]"/>
				</xsl:for-each>
			</xsl:variable>
			<xsl:if test="count($nets[local-name()='port' and *[local-name()='IsDriver']/text()='True'])">
				<xsl:variable name="driver" as="item()">
					<out>
						<xsl:for-each select="$nets[local-name()='port' and *[local-name()='IsDriver']/text()='True']">
							<xsl:variable name="drv" as="item()*" select="f:normalizeConceptNames(
										translate(*[local-name()='ConceptInstanceName']/text(),'.','_'),
										(*[local-name()='ConceptName']/text(),*[local-name()='Name']/text())[1]
									)"/>
							<xsl:for-each select="$drv">
								<ConceptInstanceName><xsl:value-of select="@ci"/></ConceptInstanceName>
								<ConceptName><xsl:value-of select="@cn"/></ConceptName>
							</xsl:for-each>
						</xsl:for-each>
					</out>
				</xsl:variable>
				<xsl:variable name="lvds_rx" select="matches(($driver//*[local-name()='ConceptInstanceName'])[1]/text(),'^P\d+_\d+_\d+')"/>
				<xsl:variable name="lvdsP" select="replace(($driver//*[local-name()='ConceptInstanceName'])[1]/text(),'^(P\d+)_\d+_(\d+)$','$1_$2')"/>
				<xsl:variable name="lvdsN" select="replace(($driver//*[local-name()='ConceptInstanceName'])[1]/text(),'^(P\d+)_(\d+)_\d+$','$1_$2')"/>
				<xsl:for-each select="$driver//*[local-name()='ConceptName']/text()">
					<xsl:variable name="outname" select="."/>
					<xsl:for-each select="$nets[local-name()='port' and *[local-name()='IsDriver']/text()='False']">
						<xsl:variable name="sink" select="."/>
						<xsl:variable name="allnames" select="f:normalizeConceptNames(
									translate($sink/*[local-name()='ConceptInstanceName']/text(),'.','_'),
									normalize-space(($sink/*[local-name()='ConceptName']/text(),$sink/*[local-name()='Name']/text())[1])
									)"/>
						<xsl:for-each select="$allnames">
							<xsl:choose>
								<xsl:when test="$lvds_rx and not(ends-with(@cn,'P') or ends-with(@cn,'N'))"/>
								<xsl:when test="not($lvds_rx) and (ends-with(@cn,'P') or ends-with(@cn,'N')) and contains(string-join(('.',$allnames/@cn,'.'),'|'),concat('|',substring(@cn,1,string-length(@cn)-1),'|'))"/>
								<xsl:otherwise>
									<net2>
										<in>
											<ConceptInstanceName><xsl:value-of select="@ci"/></ConceptInstanceName>
											<ConceptName><xsl:value-of select="@cn"/></ConceptName>
										</in>
										<out>
											<ConceptInstanceName>
												<xsl:choose>
													<xsl:when test="$lvds_rx and ends-with(@cn,'N')"><xsl:value-of select="$lvdsN"/></xsl:when>
													<xsl:otherwise><xsl:value-of select="$lvdsP"/></xsl:otherwise>
												</xsl:choose>
											</ConceptInstanceName>
											<ConceptName><xsl:value-of select="replace($outname,'^OUT.*$','OUT')"/></ConceptName>
										</out>
									</net2>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:for-each>
					</xsl:for-each>
				</xsl:for-each>
			</xsl:if>
			<xsl:if test="count($nets[local-name()='socket']) ge 2">
				<xsl:variable name="driver" as="item()*">
					<xsl:for-each select="$nets[local-name()='socket']">
						<socket>
							<xsl:copy-of select="f:normalizeConceptNames(
										translate(*[local-name()='ConceptInstanceName']/text(),'.','_'),
										(*[local-name()='ConceptName']/text(),*[local-name()='Name']/text())[1]
									)"/>
						</socket>
					</xsl:for-each>
				</xsl:variable>
				<xsl:for-each select="$driver[1]/*">
					<xsl:variable name="outer" select="."/>
					<xsl:for-each select="$driver[position()!=1]/*">
						<net2 socket="1">
							<in>
								<ConceptInstanceName><xsl:value-of select="@ci"/></ConceptInstanceName>
								<ConceptName><xsl:value-of select="concat(@cn,'_in')"/></ConceptName>
							</in>
							<out>
								<ConceptInstanceName><xsl:value-of select="$outer/@ci"/></ConceptInstanceName>
								<ConceptName><xsl:value-of select="$outer/@cn"/></ConceptName>
							</out>
						</net2>
						<net2 socket="1">
							<in>
								<ConceptInstanceName><xsl:value-of select="$outer/@ci"/></ConceptInstanceName>
								<ConceptName><xsl:value-of select="concat($outer/@cn,'_in')"/></ConceptName>
							</in>
							<out>
								<ConceptInstanceName><xsl:value-of select="@ci"/></ConceptInstanceName>
								<ConceptName><xsl:value-of select="@cn"/></ConceptName>
							</out>
						</net2>
					</xsl:for-each>
				</xsl:for-each>
			</xsl:if>
		</xsl:for-each>
	</xsl:variable>
	<xsl:function name="f:isBuilt" as="xs:boolean">
		<xsl:param name="rawinst"/>
		<xsl:sequence select="count($ParaMaps2/*[local-name()=$rawinst]) != 0"/>
	</xsl:function>
	<xsl:function name="f:calcHidden" as="xs:boolean">
		<xsl:param name="pn" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:variable name="key" select="replace($pn,'^\$\{(.*)\}$','$1')"/>
		<xsl:choose>
			<xsl:when test="$ParaMaps2/key('parameter',concat($context,':',$key))"><!-- parameter existence check: Return its Hidden attribute -->
				<xsl:value-of select="f:booleanEssence(string($ParaMaps2/key('parameter',concat($context,':',$key))/@Hidden),$context) != 0"/>
			</xsl:when>
			<xsl:otherwise><!-- Return True if formula evaluates to non-zero -->
				<xsl:value-of select="f:booleanEssence(replace(replace($pn,'&amp;lt;','&lt;'),'&amp;gt;','&gt;'),$context) != 0"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
 	<xsl:function name="f:resolveNames" as="xs:string*">
		<xsl:param name="net"/><!-- $Connects/in or $Connects/out -->
		<xsl:variable name="rawinst" select="$net/*[local-name()='ConceptInstanceName']/text()"/>
		<xsl:variable name="instance" as="item()*">
			<xsl:variable name="trial">
				<xsl:choose>
					<xsl:when test="matches($rawinst,'^P\d+$')">
						<xsl:variable name="index" select="replace($net/*[local-name()='ConceptName']/text(),'^pin_0?(\d+)$','$1')"/>
						<xsl:value-of select="f:locatePin(concat($rawinst,'_',$index))"/>
					</xsl:when>
					<xsl:when test="matches($rawinst,'^TOP$')">
						<xsl:value-of select="f:locatePin(upper-case($net/*[local-name()='ConceptName']/text()))"/>
					</xsl:when>
					<xsl:otherwise><xsl:value-of select="f:locatePin($rawinst)"/></xsl:otherwise>
				</xsl:choose>
			</xsl:variable>
			<xsl:choose>
				<xsl:when test="string-length($trial)">
					<xsl:element name="{substring-before($trial,'_')}">
						<xsl:attribute name="Int_Class_ID" select="$trial"/>
						<ParamDecl Name="inst"><Value><xsl:value-of select="substring-after($trial,'_')"/></Value></ParamDecl>
					</xsl:element>
				</xsl:when>
				<xsl:when test="$ParaMaps2/key('instance',upper-case($rawinst))">
					<xsl:copy-of select="$ParaMaps2/key('instance',upper-case($rawinst))"/>
				</xsl:when>
				<xsl:when test="$ParaMaps2/key('instance',concat($rawinst,'_0'))"><!-- special case: optional instance number -->
					<xsl:copy-of select="$ParaMaps2/key('instance',concat($rawinst,'_0'))"/>
				</xsl:when>
				<xsl:when test="$ParaMaps2/key('instance',concat($rawinst,'0'))"><!-- special case: legacy instance number -->
					<xsl:copy-of select="$ParaMaps2/key('instance',concat($rawinst,'0'))"/>
				</xsl:when>
				<xsl:when test="$ParaMaps2/key('instance',substring($rawinst,1,string-length($rawinst)-1))"><!-- special case: CANxy is part of CANx -->
					<xsl:copy-of select="$ParaMaps2/key('instance',substring($rawinst,1,string-length($rawinst)-1))"/>
				</xsl:when>
				<!-- xsl:otherwise>
					<xsl:message terminate="no">Unable to resolve <xsl:value-of select="$net/*[local-name()='ConceptInstanceName']/text()"/>:<xsl:value-of select="$net/*[local-name()='ConceptName']/text()"/></xsl:message>
				</xsl:otherwise -->
			</xsl:choose>
		</xsl:variable>
		<xsl:copy-of select="f:resolveNames($net,$instance)"/>
	</xsl:function>
	<xsl:function name="f:resolveNames" as="xs:string*">
		<xsl:param name="net"/><!-- $Connects/in or $Connects/out or Net/in or Net/out -->
		<xsl:param name="instance"/>
	<xsl:if test="count($net/*[local-name()='ConceptName']) gt 2"><xsl:message terminate="yes" select="$net"/></xsl:if>
		<xsl:variable name="context" select="$instance[1]/@Int_Class_ID"/>
		<xsl:variable name="cn" select="$net/*[local-name()='ConceptName']/text()"/>
		<xsl:variable name="ci" select="$net/*[local-name()='ConceptInstanceName']/text()"/>
		<!-- xsl:message terminate="no" select="concat('In ',$context,' ',$ci,':',$cn)"/ -->
		<xsl:variable name="hitsInternal" as="xs:string*">
			<xsl:for-each select="$instance[@Int_Class_ID]">
				<xsl:variable name="context" select="@Int_Class_ID"/>
				<xsl:for-each select="$ParaMaps2/*[local-name()=concat(local-name(current()),'spec')]/*[local-name()='Map' and matches($cn,@Name)]">
					<xsl:copy-of select="f:loopedName(.,$context,$ci,$cn)"/>
				</xsl:for-each>
			</xsl:for-each>
		</xsl:variable>
		<xsl:variable name="hitsExternal" as="xs:string*">
			<xsl:choose>
				<xsl:when test="contains($ci,'$')">
					<xsl:value-of select="f:calcFormulas(f:resolveParameter($ci,(),$context))"/>
					<xsl:value-of select="f:calcFormulas($cn)"/>
				</xsl:when>
				<xsl:when test="matches($ci,'^#lookup#')">
					<xsl:value-of select="f:locatePin(substring-after($ci,'#lookup#'))"/>
					<xsl:value-of select="f:calcFormulas($cn)"/>
				</xsl:when>
				<xsl:when test="matches($ci,'^P\d+_\d+$')"/><!-- skip duplicate netlist info for ports -->
<!-- 				<xsl:when test="matches($ci,'^P\d+\.\d+$')">
					<xsl:value-of select="translate($ci,'.','_')"/>
					<xsl:value-of select="f:calcFormulas($cn)"/>
				</xsl:when> -->
				<xsl:when test="matches($ci,'_\d+$')">
					<xsl:value-of select="$ci"/>
					<xsl:value-of select="f:calcFormulas($cn)"/>
				</xsl:when>
			</xsl:choose>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="count($hitsInternal[not(matches(.,'^suppress_'))])">
				<!-- primary port matches -->
				<xsl:copy-of select="$hitsInternal[not(matches(.,'^suppress_'))]"/>
			</xsl:when>
			<xsl:when test="count($hitsExternal)">
				<!-- instance names from elaborated Net definitions -->
				<xsl:copy-of select="$hitsExternal[not(matches(.,'^suppress_'))]"/>
			</xsl:when>
			<xsl:when test="count($hitsInternal)"/>
				<!-- intentionally masked by suppress_* -->
			<xsl:when test="not($instance/@Int_Class_ID)">
				<xsl:message terminate="no" select="concat('No instance for ',$ci,':',f:calcFormulas($cn))"/>
			</xsl:when>
			<xsl:when test="matches($instance[1]/@Int_Class_ID,'_\d+$')">
				<!-- signal name not matched by pattern in map -->
				<xsl:value-of select="$instance[1]/@Int_Class_ID"/>
				<xsl:value-of select="f:calcFormulas($cn)"/>
			</xsl:when>
			<xsl:otherwise>
				<!-- default is instance number 0 (omitted sometimes for historical reasons -->
				<xsl:value-of select="concat($instance[1]/@Int_Class_ID,'_0')"/>
				<xsl:value-of select="f:calcFormulas($cn)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- elaborate a potentially loop'ed port mapping definition -->
	<xsl:function name="f:loopedName" as="item()*">
		<xsl:param name="template" as="item()"/><!-- Map element -->
		<xsl:param name="context" as="xs:string"/>
		<xsl:param name="ci" as="xs:string"/>
		<xsl:param name="cn" as="xs:string"/>
		<xsl:choose>  
			<xsl:when test="$template/@*[local-name()!='Name' and local-name()!='Hidden']">
				<xsl:variable name="dims" select="f:enumerate(f:resolveParameter(string(($template/@*[local-name()!='Hidden' and local-name()!='Name'])[1]),(),$context),$context)"/>
				<xsl:for-each select="$dims">
					<xsl:variable name="variant" as="item()">
						<xsl:element name="{name($template)}">
							<xsl:copy-of select="($template/@*[local-name()!='Hidden' and local-name()!='Name'])[position()!=1]"/>
							<xsl:copy-of select="$template/@*[local-name()='Name']"/>
							<xsl:apply-templates mode="clone" select="$template/@Hidden|$template/*">
								<xsl:with-param tunnel="yes" name="loopvar" select="concat('\$\{',local-name(($template/@*[local-name()!='Hidden' and local-name()!='Name'])[1]),'\}')"/>
								<xsl:with-param tunnel="yes" name="loopval" select="."/>
							</xsl:apply-templates>
						</xsl:element>
					</xsl:variable>
					<xsl:copy-of select="f:loopedName($variant,$context,$ci,$cn)"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$template/@*[local-name()='Hidden']">
				<xsl:variable name="MapHidden" as="xs:string*">
					<xsl:choose>
						<xsl:when test="contains($template/@*[local-name()='Hidden'],'#')">
							<xsl:variable name="lastletter" select="string-length(substring-before(' ABCDEFGHIJKLMNOPQRSTUVWXYZx',substring($cn,string-length($cn)))) - 1" as="xs:integer"/>
							<xsl:variable name="prelastletter" select="string-length(substring-before(' ABCDEFGHIJKLMNOPQRSTUVWXYZx',substring($cn,string-length($cn) - 1,1))) - 1" as="xs:integer"/>
							<xsl:value-of select="replace(replace($template/@*[local-name()='Hidden'],'#lastletter#',string($lastletter)),'#prelastletter#',string($prelastletter))"/>
						</xsl:when>
						<xsl:otherwise><xsl:value-of select="$template/@*[local-name()='Hidden']"/></xsl:otherwise><!--TODO replace local variables -->
					</xsl:choose>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="matches($MapHidden,'^\$\{(.*?)\}$') and f:calcHidden($MapHidden,$context)"/><!-- Hidden refers to a single parameter name -->
					<xsl:when test="not(matches($MapHidden,'^\$\{(.*?)\}$')) and f:calcHidden(replace($cn,$template/@Name,f:resolveParameter($MapHidden,(),$context)),$context)"/><!-- Hidden refers to the port name -->
					<!--TODO Hidden contains formula -->
					<xsl:otherwise>
						<xsl:variable name="variant" as="item()">
							<xsl:element name="{name($template)}">
								<xsl:copy-of select="$template/@*[local-name()!='Hidden']"/>
								<xsl:copy-of select="$template/*"/>
							</xsl:element>
						</xsl:variable>
						<xsl:copy-of select="f:loopedName($variant,$context,$ci,$cn)"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:variable name="nci" as="xs:string*">
					<xsl:choose>
						<xsl:when test="contains($template/*[local-name()='ConceptInstanceName']/text(),'#lastdigit#')">
							<xsl:variable name="lastdigit" select="substring($ci,string-length($ci))"/>
							<xsl:if test="$lastdigit castable as xs:integer">
								<xsl:value-of select="f:calcFormulas(replace($cn,$template/@Name,f:resolveParameter(replace($template/*[local-name()='ConceptInstanceName']/text(),'#lastdigit#',$lastdigit),(),$context)))"/>
							</xsl:if>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="f:calcFormulas(replace($cn,$template/@Name,f:resolveParameter($template/*[local-name()='ConceptInstanceName']/text(),(),$context)))"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:variable name="ncn" as="xs:string*">
					<xsl:choose>
						<xsl:when test="contains($template/*[local-name()='ConceptName']/text(),'#lastletter#')">
							<xsl:variable name="lastletter" select="string-length(substring-before(' ABCDEFGHIJKLMNOPQRSTUVWXYZx',substring($cn,string-length($cn)))) - 1" as="xs:integer"/>
							<xsl:if test="$lastletter ge 0">
								<xsl:value-of select="f:calcFormulas(replace($cn,$template/@Name,f:resolveParameter(replace($template/*[local-name()='ConceptName']/text(),'#lastletter#',string($lastletter)),(),$context)))"/>
							</xsl:if>
						</xsl:when>
						<xsl:when test="contains($template/*[local-name()='ConceptName']/text(),'#prelastletter#')">
							<xsl:variable name="prelastletter" select="string-length(substring-before(' ABCDEFGHIJKLMNOPQRSTUVWXYZx',substring($cn,string-length($cn) - 1,1))) - 1" as="xs:integer"/>
							<xsl:if test="$prelastletter ge 0">
								<xsl:value-of select="f:calcFormulas(replace($cn,$template/@Name,f:resolveParameter(replace($template/*[local-name()='ConceptName']/text(),'#prelastletter#',string($prelastletter)),(),$context)))"/>
							</xsl:if>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="f:calcFormulas(replace($cn,$template/@Name,f:resolveParameter($template/*[local-name()='ConceptName']/text(),(),$context)))"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:if test="string-length($nci) and string-length($ncn)">
					<xsl:value-of select="$nci"/>
					<xsl:value-of select="$ncn"/>
				</xsl:if>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:function name="f:name2Driver" as="item()*">
		<xsl:param name="rawname" as="xs:string"/>
		<xsl:param name="iomode" as="xs:string"/>
		<xsl:variable name="dummy" as="item()">
			<out>
				<xsl:choose>
					<xsl:when test="matches($rawname,'^suppress_[^_]+_\d+_')">
						<ConceptInstanceName><xsl:value-of select="replace($rawname,'^suppress_([^_]+_\d+)_.*$','$1')"/></ConceptInstanceName>
						<ConceptName><xsl:value-of select="replace($rawname,'^suppress_[^_]+_\d+_(.*)$','suppress_$1')"/></ConceptName>
					</xsl:when>
					<xsl:when test="matches($rawname,'^suppress_[^_]+_')">
						<ConceptInstanceName><xsl:value-of select="replace($rawname,'^suppress_([^_]+)_.*$','$1')"/></ConceptInstanceName>
						<ConceptName><xsl:value-of select="replace($rawname,'^suppress_[^_]+_(.*)$','suppress_$1')"/></ConceptName>
					</xsl:when>
					<xsl:when test="matches($rawname,'^[^_]+_\d+_')">
						<ConceptInstanceName><xsl:value-of select="replace($rawname,'^([^_]+_\d+)_.*$','$1')"/></ConceptInstanceName>
						<ConceptName><xsl:value-of select="replace($rawname,'^[^_]+_\d+_(.*)$','$1')"/></ConceptName>
					</xsl:when>
					<xsl:when test="matches($rawname,'^[^_]+_')">
						<ConceptInstanceName><xsl:value-of select="substring-before($rawname,'_')"/></ConceptInstanceName>
						<ConceptName><xsl:value-of select="substring-after($rawname,'_')"/></ConceptName>
					</xsl:when>
					<xsl:when test="matches($rawname,'^TDO$')">
						<ConceptInstanceName><xsl:value-of select="'TCU'"/></ConceptInstanceName>
						<ConceptName><xsl:value-of select="$rawname"/></ConceptName>
					</xsl:when>
					<xsl:when test="matches($rawname,'^DAP\d+$')">
						<ConceptInstanceName><xsl:value-of select="'TCU'"/></ConceptInstanceName>
						<ConceptName><xsl:value-of select="lower-case($rawname)"/></ConceptName>
					</xsl:when>
					<xsl:when test="matches($rawname,'^DAPE\d+$')"><!-- Patch for A2G: DAPE_ED output via dedicated pin only! -->
						<ConceptInstanceName><xsl:if test="$iomode!='DEDICATED'">suppress_</xsl:if><xsl:value-of select="'DAPE_1'"/></ConceptInstanceName>
						<ConceptName><xsl:if test="$iomode!='DEDICATED'">suppress_</xsl:if><xsl:value-of select="replace($rawname,'DAPE(\d+)$','DAP$1')"/></ConceptName>						
					</xsl:when>
					<xsl:when test="matches($rawname,'^XTAL\d+$','i')">
						<ConceptInstanceName><xsl:value-of select="'CCU'"/></ConceptInstanceName>
						<ConceptName><xsl:value-of select="upper-case($rawname)"/></ConceptName>
					</xsl:when>
					<xsl:otherwise>
						<ConceptInstanceName><xsl:value-of select="'OCDS'"/></ConceptInstanceName>
						<ConceptName><xsl:value-of select="$rawname"/></ConceptName>
					</xsl:otherwise>
				</xsl:choose>
			</out>
		</xsl:variable>
		<xsl:variable name="outputname" as="xs:string*" select="f:resolveNames($dummy)"/>	
		<xsl:for-each select="for $i in 1 to count($outputname) return $i">
			<xsl:if test="current() mod 2 = 1">
				<spirit:internalPortReference>
					<xsl:attribute name="spirit:componentRef" select="$outputname[current()]"/>
					<xsl:attribute name="spirit:portRef" select="$outputname[current() + 1]"/>
				</spirit:internalPortReference>						
			</xsl:if>
		</xsl:for-each>
	</xsl:function>
	<!-- elaborate a potentially loop'ed resource instance definition -->
	<xsl:function name="f:makeResourceInstance" as="item()*">
		<xsl:param name="template" as="item()"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:choose>
			<xsl:when test="$template/@*[local-name()!='Hidden']">
				<xsl:variable name="dims" select="f:enumerate(f:resolveParameter(string(($template/@*[local-name()!='Hidden'])[1]),(),$context),$context)"/>
				<xsl:for-each select="$dims">
					<xsl:variable name="variant" as="item()">
						<xsl:element name="{name($template)}">
							<xsl:copy-of select="($template/@*[local-name()!='Hidden'])[position()!=1]"/>
							<xsl:apply-templates mode="clone" select="$template/@Hidden|$template/*">
								<xsl:with-param tunnel="yes" name="loopvar" select="concat('\$\{',local-name(($template/@*[local-name()!='Hidden'])[1]),'\}')"/>
								<xsl:with-param tunnel="yes" name="loopval" select="."/>
							</xsl:apply-templates>
						</xsl:element>
					</xsl:variable>
					<xsl:copy-of select="f:makeResourceInstance($variant,$context)"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$template/@*[local-name()='Hidden'] and matches($template/@*[local-name()='Hidden'],'^\$\{(.*?)\}$') and f:calcHidden(string($template/@*[local-name()='Hidden']),$context)"/>
			<xsl:when test="$template/@*[local-name()='Hidden'] and not(matches($template/@*[local-name()='Hidden'],'^\$\{(.*?)\}$')) and f:calcHidden(f:resolveParameter($template/@*[local-name()='Hidden'],(),$context),$context)"/>
			<xsl:otherwise>
				<spirit:componentInstance>
					<spirit:instanceName>
						<xsl:value-of select="f:calcFormulas(f:resolveParameter($template/*[local-name()='ConceptInstanceName']/text(),(),$context))"/>
					</spirit:instanceName>
					<xsl:variable name="VLNV" select="tokenize($template/*[local-name()='VLNV']/text(),':')"/>
					<spirit:componentRef spirit:vendor="{$VLNV[1]}" spirit:library="{$VLNV[2]}" spirit:name="{$VLNV[3]}" spirit:version="{$VLNV[4]}"/>
					<xsl:if test="$template/*[local-name()='ParamDecl']">
						<spirit:configurableElementValues>
							<xsl:for-each select="$template/*[local-name()='ParamDecl']">
								<spirit:configurableElementValue spirit:referenceId="{@Name}">
									<xsl:value-of select="f:calcFormulas(f:resolveParameter(*[local-name()='Value']/text(),(),$context))"/>
								</spirit:configurableElementValue>
							</xsl:for-each>
						</spirit:configurableElementValues>
					</xsl:if>
					<xsl:if test="$template/*[local-name()='Constraint']">
						<spirit:vendorExtensions>
							<xsl:for-each select="$template/*[local-name()='Constraint']">
								<xsl:copy-of select="f:loopedConstraint(.,$context)"/>
							</xsl:for-each>
						</spirit:vendorExtensions>
					</xsl:if>
				</spirit:componentInstance>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- elaborate a potentially loop'ed port constrain -->
	<xsl:function name="f:loopedConstraint" as="item()*">
		<xsl:param name="template" as="item()"/><!-- Map element -->
		<xsl:param name="context" as="xs:string"/>
		<xsl:choose>  
			<xsl:when test="$template/@*">
				<xsl:variable name="dims" select="f:enumerate(f:resolveParameter(string(($template/@*)[1]),(),$context),$context)"/>
				<xsl:for-each select="$dims">
					<xsl:variable name="variant" as="item()">
						<xsl:element name="{name($template)}">
							<xsl:copy-of select="($template/@*)[position()!=1]"/>
							<xsl:apply-templates mode="clone" select="$template/@Hidden|$template/*">
								<xsl:with-param tunnel="yes" name="loopvar" select="concat('\$\{',local-name(($template/@*[local-name()!='Hidden' and local-name()!='Name'])[1]),'\}')"/>
								<xsl:with-param tunnel="yes" name="loopval" select="."/>
							</xsl:apply-templates>
						</xsl:element>
					</xsl:variable>
					<xsl:copy-of select="f:loopedConstraint($variant,$context)"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:otherwise>
				<xsl:apply-templates mode="clone" select="$template">
					<xsl:with-param tunnel="yes" name="loopvar" select="'\$\{inst\}'"/>
					<xsl:with-param tunnel="yes" name="loopval" select="f:resolveParameter('${inst}',(),$context)"/>
				</xsl:apply-templates>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- elaborate a potentially loop'ed local interconnect definition -->
	<xsl:function name="f:makeNetInstance" as="item()*">
		<xsl:param name="template" as="item()"/>
		<xsl:param name="instance" as="item()"/>
		<xsl:variable name="context" as="xs:string" select="$instance/@Int_Class_ID"/>
		<xsl:choose>
			<xsl:when test="$template/@*[local-name()!='Hidden']">
				<xsl:variable name="dims" select="f:enumerate(f:resolveParameter(string(($template/@*[local-name()!='Hidden'])[1]),(),$context),$context)"/>
				<xsl:for-each select="$dims">
					<xsl:variable name="variant" as="item()">
						<xsl:element name="{name($template)}">
							<xsl:copy-of select="($template/@*[local-name()!='Hidden'])[position()!=1]"/>
							<xsl:apply-templates mode="clone" select="$template/@Hidden|$template/*">
								<xsl:with-param tunnel="yes" name="loopvar" select="concat('\$\{',local-name(($template/@*[local-name()!='Hidden'])[1]),'\}')"/>
								<xsl:with-param tunnel="yes" name="loopval" select="."/>
							</xsl:apply-templates>
						</xsl:element>
					</xsl:variable>
					<xsl:copy-of select="f:makeNetInstance($variant,$instance)"/>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$template/@*[local-name()='Hidden'] and matches($template/@*[local-name()='Hidden'],'^\$\{(.*?)\}$') and f:calcHidden(string($template/@*[local-name()='Hidden']),$context)"/>
			<xsl:when test="$template/@*[local-name()='Hidden'] and not(matches($template/@*[local-name()='Hidden'],'^\$\{(.*?)\}$')) 
															and f:calcHidden(f:resolveParameter($template/@*[local-name()='Hidden'],(),$context),$context)"/>
			<xsl:otherwise>
				<xsl:variable name="inputname" as="xs:string*" select="f:resolveNames($template/*[local-name()='in'],$instance)"/><!-- mutex controlled list of inputs -->	
				<xsl:variable name="outputname" as="xs:string*" select="f:resolveNames($template/*[local-name()='out'],$instance)"/><!-- mutex controlled list of outputs -->
				<spirit:adHocConnection>
					<spirit:name>
						<xsl:value-of select="concat($inputname[1],'_',$inputname[2])"/>
					</spirit:name>
					<spirit:description>
						<xsl:value-of select="concat($outputname[1],'_',$outputname[2],'__',$inputname[1],'_',$inputname[2])"/>
					</spirit:description>
					<xsl:for-each select="for $i in 1 to count($inputname) return $i">
						<xsl:if test="current() mod 2 = 1">
							<spirit:internalPortReference>
								<xsl:attribute name="spirit:componentRef" select="$inputname[current()]"/>
								<xsl:attribute name="spirit:portRef" select="$inputname[current() + 1]"/>
							</spirit:internalPortReference>						
						</xsl:if>
					</xsl:for-each>
					<xsl:for-each select="for $i in 1 to count($outputname) return $i">
						<xsl:if test="current() mod 2 = 1">
							<spirit:internalPortReference>
								<xsl:attribute name="spirit:componentRef" select="$outputname[current()]"/>
								<xsl:attribute name="spirit:portRef" select="$outputname[current() + 1]"/>
							</spirit:internalPortReference>						
						</xsl:if>
					</xsl:for-each>
				</spirit:adHocConnection>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- elaborate one global sideband interconnect -->
	<xsl:function name="f:makeNet" as="item()*">
		<xsl:param name="net" as="item()"/>
		<xsl:param name="instance" as="item()"/>
		<xsl:variable name="inputname" as="xs:string*" select="f:resolveNames($net/*[local-name()='in'],$instance)"/><!-- list of broadcast receivers -->
		<xsl:variable name="outputname" as="xs:string*" select="f:resolveNames($net/*[local-name()='out'])"/><!-- mutex controlled list of drivers -->	
		<xsl:for-each select="for $i in 1 to count($inputname) return $i">
			<xsl:if test="current() mod 2 = 1">
				<spirit:adHocConnection>
					<spirit:name>
						<xsl:value-of select="concat($inputname[current()],'_',$inputname[current() + 1])"/>
					</spirit:name>
					<spirit:description>
						<xsl:value-of select="$net/*[local-name()='out']/*[local-name()='ConceptInstanceName']/text()"/><xsl:text>_</xsl:text>
						<xsl:value-of select="$net/*[local-name()='out']/*[local-name()='ConceptName']/text()"/><xsl:text>__</xsl:text>
						<xsl:value-of select="$net/*[local-name()='in']/*[local-name()='ConceptInstanceName']/text()"/><xsl:text>_</xsl:text>
						<xsl:value-of select="$net/*[local-name()='in']/*[local-name()='ConceptName']/text()"/>
					</spirit:description>
					<spirit:internalPortReference>
						<xsl:attribute name="spirit:componentRef" select="$inputname[current()]"/>
						<xsl:attribute name="spirit:portRef" select="$inputname[current() + 1]"/>
					</spirit:internalPortReference>						
					<xsl:for-each select="for $i in 1 to count($outputname) return $i">
						<xsl:if test="current() mod 2 = 1">
							<spirit:internalPortReference>
								<xsl:attribute name="spirit:componentRef" select="$outputname[current()]"/>
								<xsl:attribute name="spirit:portRef" select="$outputname[current() + 1]"/>
							</spirit:internalPortReference>						
						</xsl:if>
					</xsl:for-each>
				</spirit:adHocConnection>
			</xsl:if>
		</xsl:for-each>
	</xsl:function>
	<!-- elaborate one global socket interconnect -->
	<xsl:function name="f:makeSocketNets" as="item()*">
		<xsl:param name="net" as="item()"/>
		<xsl:param name="instance1" as="item()"/>
		<xsl:param name="instance2" as="item()"/>
		<!-- xsl:comment>Socketconnection <xsl:value-of select="$instance2/@Int_Class_ID"/> -> <xsl:value-of select="$instance1/@Int_Class_ID"/></xsl:comment -->
		<xsl:variable name="inputname" select="replace($net/*[local-name()='in']/*[local-name()='ConceptName']/text(),'(.*?)_in','$1')"/>
		<xsl:for-each select="$instance1/*[local-name()='Socket' and @Name=$inputname]">
			<xsl:for-each select="./*[local-name()='Member' and *[local-name()='Direction']/text()='in']">
				<xsl:variable name="inport" select="."/>
				<xsl:variable name="inbits" as="xs:integer*">
					<xsl:if test="./*[local-name()='Vector']">
						<xsl:variable name="nl" select="f:evaluate(./*[local-name()='Vector']/*[local-name()='Left'])"/>
						<xsl:variable name="nr" select="f:evaluate(./*[local-name()='Vector']/*[local-name()='Right'])"/>
						<xsl:choose>
							<xsl:when test="number(nl) lt number(nr)"><xsl:for-each select="for $i in xs:integer($nl) to xs:integer($nr) return $i"><xsl:value-of select="."/></xsl:for-each></xsl:when>
							<xsl:otherwise><xsl:for-each select="for $i in xs:integer($nr) to xs:integer($nl) return $i"><xsl:value-of select="."/></xsl:for-each></xsl:otherwise>
						</xsl:choose>
					</xsl:if>
				</xsl:variable>
				<xsl:variable name="wire" select="@wire"/>
				<xsl:for-each select="$instance2/*[local-name()='Socket' and @Name=$net/*[local-name()='out']/*[local-name()='ConceptName']/text()]">
					<xsl:for-each select="./*[local-name()='Member' and @wire=$wire]">
						<xsl:variable name="outport" select="."/>					
						<xsl:variable name="outbits" as="xs:integer*">
							<xsl:if test="./*[local-name()='Vector']">
								<xsl:variable name="nl" select="f:evaluate(./*[local-name()='Vector']/*[local-name()='Left'])"/>
								<xsl:variable name="nr" select="f:evaluate(./*[local-name()='Vector']/*[local-name()='Right'])"/>
								<xsl:choose>
									<xsl:when test="number(nl) lt number(nr)"><xsl:for-each select="for $i in xs:integer($nl) to xs:integer($nr) return $i"><xsl:value-of select="."/></xsl:for-each></xsl:when>
									<xsl:otherwise><xsl:for-each select="for $i in xs:integer($nr) to xs:integer($nl) return $i"><xsl:value-of select="."/></xsl:for-each></xsl:otherwise>
								</xsl:choose>
							</xsl:if>
						</xsl:variable>
						<xsl:choose>
							<xsl:when test="count($inbits)">
								<xsl:for-each select="$inbits">
									<xsl:variable name="k" select="position()"/>
									<xsl:variable name="subnet" as="item()">
										<Net>
											<in>
												<ConceptInstanceName><xsl:value-of select="$instance1/@Int_Class_ID"/></ConceptInstanceName>
												<ConceptName><xsl:value-of select="normalize-space(string-join(($inport/text()),''))"/>_<xsl:value-of select="$inbits[$k]"/></ConceptName>
											</in>
											<out>															
												<ConceptInstanceName><xsl:value-of select="$instance2/@Int_Class_ID"/></ConceptInstanceName>
												<ConceptName>
													<xsl:value-of select="normalize-space(string-join(($outport/text()),''))"/><xsl:if test="count($outbits) ge $k">_<xsl:value-of select="$outbits[$k]"/></xsl:if>
												</ConceptName>
											</out>
										</Net>
									</xsl:variable>
									<xsl:copy-of select="f:makeNet($subnet,$instance1)"/>
								</xsl:for-each>
							</xsl:when>
							<xsl:otherwise>
								<xsl:variable name="subnet" as="item()">
									<Net>
										<in>
											<ConceptInstanceName><xsl:value-of select="$instance1/@Int_Class_ID"/></ConceptInstanceName>
											<ConceptName><xsl:value-of select="normalize-space(string-join(($inport/text()),''))"/></ConceptName>
										</in>
										<out>															
											<ConceptInstanceName><xsl:value-of select="$instance2/@Int_Class_ID"/></ConceptInstanceName>
											<ConceptName>
												<xsl:value-of select="normalize-space(string-join(($outport/text()),''))"/><xsl:if test="count($outbits) ge 1">_<xsl:value-of select="$outbits[1]"/></xsl:if>
											</ConceptName>
										</out>
									</Net>
								</xsl:variable>
								<xsl:copy-of select="f:makeNet($subnet,$instance1)"/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:for-each>
				</xsl:for-each>
			</xsl:for-each>
		</xsl:for-each>
	</xsl:function>
	<!-- loop unrolling templates -->
	<xsl:template match="text()" mode="clone">
		<xsl:param tunnel="yes" name="loopvar"/>
		<xsl:param tunnel="yes" name="loopval"/>
		<xsl:value-of select="replace(.,$loopvar,$loopval)"/>
	</xsl:template>
	<xsl:template match="@*" mode="clone">
		<xsl:param tunnel="yes" name="loopvar"/>
		<xsl:param tunnel="yes" name="loopval"/>
		<xsl:attribute name="{name()}"><xsl:value-of select="replace(string(.),$loopvar,$loopval)"/></xsl:attribute>
	</xsl:template>
	<xsl:template match="*" mode="clone">
		<xsl:copy><xsl:apply-templates mode="#current" select="@*|node()"/></xsl:copy>
	</xsl:template>
<!-- ======================================================================= -->
	<!-- global variables -->
	<xsl:variable name="created" select="format-dateTime(fn:adjust-dateTime-to-timezone(fn:current-dateTime(), xs:dayTimeDuration('PT0H')), '[Y0001]-[M01]-[D01]T[H01]:[m01]:[s01]Z')"/>
	<xsl:variable name="silicon_name" select="string (//spinner5PBuilder/properties/property[@name='chip_top_name']) "/>
	<xsl:variable name="outputfile" select="concat($Device,'_Design_Spirit_raw.xml')"/>
	<xsl:output method="xml" version="1.0" encoding="UTF-8" indent="yes"/>
	<!-- ======================================================================= -->
	<!-- topelevel -->
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
<!--
				<DEBUG>
					<xsl:copy-of select="$ParaMaps2"/>
					<xsl:copy-of select="$Connects[*/*[local-name()='ConceptInstanceName' and text()='EBU']]"/>
					<xsl:copy-of select="$Connects[*/*[local-name()='ConceptInstanceName' and text()='TOP']]"/>
					<xsl:copy-of select="$Connects[*/*[local-name()='ConceptInstanceName' and contains(text(),'DAPE')]]"/>
					<xsl:copy-of select="$Connects[starts-with(*[local-name()='in']/*[local-name()='ConceptInstanceName']/text(),'AGBT')]"/>
					<xsl:copy-of select="$Connects[*/*[local-name()='ConceptInstanceName' and starts-with(text(),'P13_0')]]"/>
					<xsl:copy-of select="$Connects[*[local-name()='in']/*[local-name()='ConceptInstanceName']/text()='SCU']"/>
				</DEBUG>
				<xsl:message terminate="yes"/>
				<DEBUG>
					<xsl:copy-of select="$Connects[*[local-name()='in']/*[local-name()='ConceptInstanceName' and text()='AGBT']]"/>
				</DEBUG>
-->
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

	<!-- Avoid built-in templates -->
	<xsl:template match="*|/">
		<xsl:apply-templates/>
	</xsl:template>
	<!-- functions -->
	<xsl:function name="f:str2index" as="xs:string">
		<xsl:param name="name" as="xs:string"/>
		<xsl:variable name="ix" select="string-length(substring-before('ABCDEFGHIJKLMNOP',upper-case(replace($name,'^.+(\D)$','$1'))))"/>
		<xsl:value-of select="xs:string($ix)"/>
	</xsl:function>
	<xsl:function name="f:str2dec" as="xs:integer">
		<xsl:param name="in" as="xs:string"/>
		<xsl:choose>
			<xsl:when test="string-length($in) &lt; 2">
				<xsl:value-of select="number($in)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="10*f:str2dec(substring($in,1,string-length($in)-1)) + number(substring($in,string-length($in)))"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- Generate a complete XMP-wrapped set of metadata using the Dublin Core semanics -->
	<xsl:template name="MetaData">
		<xsl:processing-instruction name="xpacket">begin="" id="W5M0MpCehiHzreSzNTczkc9d"</xsl:processing-instruction>
		<xsl:element name="x:xmpmeta" namespace="adobe:ns:meta/">
			<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/">
				<rdf:Description rdf:about="">
					<dc:title>
						<rdf:Alt>
							<rdf:li xml:lang="en">
								<xsl:value-of select="$Device"/> On-chip Connectivity Definitions</rdf:li>
						</rdf:Alt>
					</dc:title>
					<dc:creator>
						<rdf:Seq>
							<rdf:li>CTDD@infineon.com</rdf:li>
						</rdf:Seq>
					</dc:creator>
					<dc:subject>
						<rdf:Bag>
							<rdf:li>
								<xsl:value-of select="$Device"/>
							</rdf:li>
							<rdf:li>
								<xsl:value-of select="$family"/>
							</rdf:li>
							<rdf:li>Resource modelling</rdf:li>
							<rdf:li>Resource mapping</rdf:li>
							<rdf:li>SPIRIT</rdf:li>
						</rdf:Bag>
					</dc:subject>
					<dc:description>
						<rdf:Alt>
							<rdf:li xml:lang="en">SPIRIT (IEEE Std 1685-2009) compliant definition of connectivity.</rdf:li>
						</rdf:Alt>
					</dc:description>
					<dc:publisher>http://www.infineon.com</dc:publisher>
					<dc:contributor>
						<rdf:Seq>
							<rdf:li>IFX ATV MC ACE</rdf:li>
						</rdf:Seq>
					</dc:contributor>
					<dc:date>
						<xsl:value-of select="$created"/>
					</dc:date>
					<!-- don't use  xsi:type="dcterms:W3CDTF" -->
					<dc:type>Dataset</dc:type>
					<!-- don't use  xsi:type="dcterms:DCMIType" -->
					<dc:format>application/xml</dc:format>
					<dc:identifier>
						<xsl:value-of select="replace($outputfile,'_raw','')"/>
					</dc:identifier>
					<dc:source>
						<xsl:value-of select="concat($silicon_name,'.spinner@@',$label)"/>
					</dc:source>
					<dc:language>
						<rdf:Bag>
							<rdf:li>en</rdf:li>
						</rdf:Bag>
					</dc:language>
					<dc:relation>
						<rdf:Bag>
							<rdf:li>
								<xsl:value-of select="$Device"/> Data Sheet</rdf:li>
						</rdf:Bag>
					</dc:relation>
					<dc:coverage>
						<rdf:Alt>
							<rdf:li xml:lang="en">Legal Disclaimer: 
The information given in this document shall in no event be regarded as a guarantee of conditions or
characteristics. With respect to any examples or hints given herein, any typical values stated herein and/or any
information regarding the application of the device, Infineon Technologies hereby disclaims any and all warranties
and liabilities of any kind, including without limitation, warranties of non-infringement of intellectual property rights
of any third party.
								</rdf:li>
						</rdf:Alt>
					</dc:coverage>
					<dc:rights>
						<rdf:Alt>
							<rdf:li xml:lang="en">Copyright 2013 Infineon Technologies AG. All Rights Reserved</rdf:li>
						</rdf:Alt>
					</dc:rights>
				</rdf:Description>
			</rdf:RDF>
		</xsl:element>
		<xsl:processing-instruction name="xpacket">end="'w'"</xsl:processing-instruction>
	</xsl:template>
	<!-- stuff copied from ExcelConst2Essence.xslt -->
	<!-- Excel handling -->				
	<xsl:function name="f:readExcelCSV" as="item()*"><!-- array of <row> -->
		<xsl:param name="filename" as="xs:string"/>
		<xsl:variable name="temp" as="xs:string*">
			<xsl:analyze-string select="unparsed-text($filename,'iso-8859-1')" regex='".*?"' flags="s">
				<xsl:matching-substring>
					<xsl:value-of select="translate(normalize-space(.),';','^')"/>
				</xsl:matching-substring>
				<xsl:non-matching-substring>
					<xsl:value-of select="."/>
				</xsl:non-matching-substring>
			</xsl:analyze-string>
		</xsl:variable>
		<xsl:analyze-string select="string-join($temp,'')" regex="\n+">
			<xsl:non-matching-substring>
				<row>
					<xsl:attribute name="n" select="xs:integer((position()+1) div 2)"/>
					<xsl:for-each select="tokenize(.,';')">
						<col>
							<xsl:value-of select="translate(normalize-space(.),'^',';')"/>
						</col>								
					</xsl:for-each>
				</row>
			</xsl:non-matching-substring>
		</xsl:analyze-string>
	</xsl:function>
	<xsl:function name="f:tokenizeExcel" as="item()*"><!-- array of <header> -->
		<xsl:param name="excel" as="item()*"/><!-- array of <row> -->
		<xsl:for-each select="$excel">
			<xsl:choose>
				<xsl:when test="not(./*[local-name()='col' and text()='Bitfield'])"/>
				<xsl:when test="not(./*[local-name()='col' and text()='Indices'])"/>
				<xsl:when test="not(./*[local-name()='col' and text()='Value'])"/>
				<xsl:when test="not(./*[local-name()='col' and text()='Symbol'])"/>
				<xsl:when test="not(./*[local-name()='col' and text()='Description'])"/>
				<xsl:otherwise>
					<header>										
						<xsl:attribute name="start" select="./@n"/>
						<xsl:for-each select="./*">
							<xsl:choose>
								<xsl:when test="text()='Bitfield'"><xsl:attribute name="Bitfield" select="position()"/></xsl:when>
								<xsl:when test="text()='Indices'"><xsl:attribute name="Indices" select="position()"/></xsl:when>
								<xsl:when test="text()='Value'"><xsl:attribute name="Value" select="position()"/></xsl:when>
								<xsl:when test="text()='Symbol'"><xsl:attribute name="Symbol" select="position()"/></xsl:when>
								<xsl:when test="text()='AltSymbol'"><xsl:attribute name="AltSymbol" select="position()"/></xsl:when>
								<xsl:when test="text()='Description'"><xsl:attribute name="Description" select="position()"/></xsl:when>
								<xsl:when test="text()='Filter'"><xsl:attribute name="Filter" select="position()"/></xsl:when>
							</xsl:choose>
						</xsl:for-each>
					</header>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:for-each>
	</xsl:function>			
	<!-- -->
</xsl:stylesheet>
