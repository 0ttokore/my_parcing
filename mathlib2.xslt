<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:f="http://www.infineon.com">
	<xsl:param name="warning" as="xs:string" select="'recover'"/>
	<!-- fault behavior: "fatal" means "stop on first problem" -->
	<!-- GTM workaround -->
	<xsl:param name="suppress" as="xs:string" select="''"/><!-- set to ##suppress## in invocation line -->
	<!-- file lookup -->
	<xsl:function name="f:resolvePath" as="xs:string">
		<xsl:param name="paths" as="xs:string"/>
		<xsl:param name="file" as="xs:string"/>
		<xsl:variable name="files" as="xs:string*">
			<xsl:for-each select="tokenize($paths,',')">
				<xsl:variable name="this" select="concat(normalize-space(.),normalize-space($file))"/>
				<xsl:if test="doc-available($this)">
					<xsl:value-of select="$this"/>
				</xsl:if>
			</xsl:for-each>
			<xsl:value-of select="normalize-space($file)"/>
		</xsl:variable>
		<xsl:value-of select="$files[1]"/>
	</xsl:function>
	<!-- parameter lookup -->
	<xsl:function name="f:getparameter" as="xs:string">
		<xsl:param name="pn" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:variable name="key" as="xs:string">
			<xsl:choose>
				<xsl:when test="starts-with($pn,'\{')">
					<xsl:value-of select="replace($pn,'^\{(.*)\}.*$','$1')"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$pn"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="not($ParaMaps2/*[string(@Int_Class_ID)=$context])">
				<xsl:message terminate="yes">ERROR: Undefined context <xsl:value-of select="$context"/> for parameter "<xsl:value-of select="$key"/>"
				</xsl:message>
				<xsl:text>?</xsl:text>
			</xsl:when>
			<xsl:when test="$key='suppress' and string-length($suppress)"><xsl:value-of select="$suppress"/></xsl:when>
			<xsl:when test="$ParaMaps2/key('parameter',concat($context,':',$key))">
				<xsl:variable name="list" as="xs:string*">
					<xsl:for-each select="$ParaMaps2/key('parameter',concat($context,':',$key))/*[ends-with(local-name(),'Value')]">
						<xsl:sort data-type="number" select="string-length(local-name())"/>
						<xsl:value-of select="text()"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="$list[1]"/>
			</xsl:when>
			<xsl:when test="starts-with($key,'$') and $ParaMaps2/key('parameter',concat($context,':',substring($key,2)))">
				<xsl:variable name="list" as="xs:string*">
					<xsl:for-each select="$ParaMaps2/key('parameter',concat($context,':',substring($key,2)))/*[ends-with(local-name(),'Value')]">
						<xsl:sort data-type="number" select="string-length(local-name())"/>
						<xsl:value-of select="text()"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="$list[1]"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}" select="string-join(('ERROR: Undefined parameter',
						$pn,'in Context',$ParaMaps2/*[@Int_Class_ID=$context]/@InstanceName,concat('[',$context,']')),' ')"/>
				<xsl:message terminate="no">Keeping value as "<xsl:value-of select="$pn"/>"</xsl:message>
				<xsl:value-of select="$pn"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:function name="f:getfilter" as="xs:string*"><!-- undefined is taken as empty string -->
		<xsl:param name="pn" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:variable name="key" as="xs:string">
			<xsl:choose>
				<xsl:when test="starts-with($pn,'\{')">
					<xsl:value-of select="replace($pn,'^\{(.*)\}.*$','$1')"/>
				</xsl:when>
				<xsl:otherwise>
					<xsl:value-of select="$pn"/>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="not($ParaMaps2/filter[@Int_Class_ID=$context])">
				<xsl:message terminate="yes">ERROR: Undefined context <xsl:value-of select="$context"/>
				</xsl:message>
				<xsl:text>?</xsl:text>
			</xsl:when>
			<xsl:when test="$ParaMaps2/key('filter',concat($context,':',$key))">
				<xsl:variable name="list" as="xs:string*">
					<xsl:for-each select="$ParaMaps2/key('filter',concat($context,':',$key))/*[ends-with(local-name(),'Value')]">
						<xsl:sort data-type="number" select="string-length(local-name())"/>
						<xsl:value-of select="text()"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="$list[1]"/>
			</xsl:when>
		</xsl:choose>
	</xsl:function>
	<!-- unroll quoted parameter references -->
	<xsl:function name="f:unquote" as="xs:string">
		<xsl:param name="in" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:choose>
			<xsl:when test="matches($in,'^&quot;\$.+?&quot;$')">
				<xsl:copy-of select="f:unquote(replace($in,'^&quot;(\$.+)&quot;$','$1'),$context)"/>
			</xsl:when>
			<xsl:when test='matches($in,"^&apos;\$.+?&apos;$")'>
				<xsl:copy-of select='f:unquote(replace($in,"^&apos;(\$.+)&apos;$","$1"),$context)'/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy-of select="$in"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- -->
	<xsl:function name="f:resolveParameter" as="xs:string">
		<xsl:param name="in" as="xs:string"/>
		<xsl:param name="keep" as="xs:string*"/>
		<xsl:value-of select="f:resolveParameter($in,$keep,'0')"/>
	</xsl:function>
	<xsl:function name="f:resolveParameter" as="xs:string">
		<xsl:param name="in" as="xs:string"/>
		<xsl:param name="keep" as="xs:string*"/>
		<xsl:param name="context" as="xs:string*"/>
		<xsl:choose>
			<xsl:when test="contains($in,'${')">
				<xsl:variable name="key" select="substring-after($in,'${')"/>
				<xsl:variable name="t1" select="substring-before($key,'}')"/>
				<xsl:variable name="t2" select="substring-before($key,'&quot;')"/>
				<xsl:variable name="t3" select="substring-before($key,'${')"/>
				<xsl:variable name="para" as="xs:string*">
					<xsl:choose>
						<xsl:when test="substring($key,1,1)='&quot;'">
							<xsl:variable name="t30" select="substring($key,2)"/>
							<xsl:variable name="t40" select="substring-before($t30,'&quot;')"/>
							<xsl:variable name="t50" select="substring-after($t30,'&quot;')"/>
							<xsl:if test="contains($t50,'}')">
								<xsl:variable name="t60" select="substring-before($t50,'}')"/>
								<xsl:copy-of select="concat('&quot;',$t40,'&quot;',$t60)"/><!--TODO evaluate t60 -->
								<xsl:if test="string-length(substring-after($t50,'}'))">
									<xsl:copy-of select="f:resolveParameter(substring-after($t50,'}'),$keep,$context)"/>
								</xsl:if>
							</xsl:if>
						</xsl:when>
						<xsl:when test="string-length($t2) &gt; 0 and string-length($t2) &lt; string-length($t1)">
							<xsl:variable name="t30" select="substring-after($key,'&quot;')"/>
							<xsl:variable name="t40" select="substring-before($t30,'&quot;')"/>
							<xsl:variable name="t50" select="substring-after($t30,'&quot;')"/>
							<xsl:variable name="t60" select="substring-before($t50,'}')"/>
							<xsl:copy-of select="concat($t2,'&quot;',$t40,'&quot;',$t60)"/><!--TODO evaluate t60 -->
							<xsl:if test="string-length(substring-after($t50,'}'))">
								<xsl:copy-of select="f:resolveParameter(substring-after($t50,'}'),$keep,$context)"/>
							</xsl:if>
						</xsl:when>
						<xsl:when test="string-length($key)=0">
							<xsl:value-of select="'${'"/>
						</xsl:when>
						<xsl:when test="contains($key,'${') and string-length($t3) &lt; string-length($t1)">
							<xsl:value-of select="'${'"/>
							<xsl:copy-of select="f:resolveParameter($key,$keep,$context)"/>
						</xsl:when>
						<xsl:when test="contains($t1,'$')">
							<xsl:value-of select="'${'"/>
							<xsl:copy-of select="f:resolveParameter($key,$keep,$context)"/>
						</xsl:when>
						<xsl:otherwise>
							<xsl:copy-of select="$t1"/>
							<xsl:if test="string-length(substring-after($key,'}'))">
								<xsl:copy-of select="f:resolveParameter(substring-after($key,'}'),$keep,$context)"/>
							</xsl:if>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="string-length($para[1])=0"><!-- left half of nested expression -->
						<xsl:copy-of select="$in"/>
						<!-- xsl:value-of select="substring-before($in,'${')"/ -->
					</xsl:when>
					<xsl:when test="$para[1]=$keep or contains($para[1],'$') or contains($para[1],'+')">
						<xsl:value-of select="string-join((substring-before($in,'${'),$para),'')"/>
					</xsl:when>
					<xsl:when test="$para[1]=('&quot;{&quot;','&quot;}&quot;')">
						<xsl:value-of select="string-join((substring-before($in,'${'),substring($para[1],2,1),$para[2]),'')"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:variable name="p" select="translate(f:getparameter($para[1],$context),'&quot;','')"/>
						<xsl:variable name="q" select='translate($p,"&apos;","")'/>
						<xsl:variable name="r" select="replace($q,'&amp;amp;','&amp;')"/>
						<xsl:value-of select="string-join((substring-before($in,'${'),$r,$para[2]),'')"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy-of select="$in"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:function name="f:minimizeParameter" as="xs:string"><!-- elaborate or flatten indices -->
		<xsl:param name="in" as="xs:string"/>
		<xsl:param name="varmap" as="item()*"/>
		<xsl:param name="context" as="xs:string*"/>
		<xsl:choose>
			<xsl:when test="contains($in,'${')">
				<xsl:variable name="key" select="substring-after($in,'${')"/>
				<xsl:variable name="paralength" select="f:findClosingCurly($key,0)"/>
				<xsl:if test="$paralength=0">
					<xsl:message terminate="yes" select="concat('ERROR: No closing } in {',$key)"/>
				</xsl:if>
				<xsl:variable name="para" select="normalize-space(substring($key,1,$paralength -1))"/>
				<xsl:choose>
					<xsl:when test="contains($para,'${')">
						<xsl:value-of select="concat(substring-before($in,'${'),
								'${',f:minimizeParameter(substring($key,1,$paralength),$varmap,$context),
								f:minimizeParameter(substring($key,$paralength+1),$varmap,$context))"/>
					</xsl:when>
					<xsl:when test="count($varmap[@Name=replace($para,'^\$','')])=1">
						<xsl:value-of select="concat(substring-before($in,'${'),
								$varmap[@Name=replace($para,'^\$','')],
								f:minimizeParameter(substring-after($key,'}'),$varmap,$context))"/>
					</xsl:when>
					<xsl:when test="matches($para,'^\$[a-z]$')"><!-- ${$x} but unknown x -->
								<xsl:value-of select="concat(substring-before($in,'${'),
								substring($para,2),
								f:minimizeParameter(substring($key,$paralength+1),$varmap,$context))"/>
					</xsl:when>
					<xsl:when test="$ParaMaps2/key('parameter',concat($context,':',replace($para,'^\$','')))">
						<xsl:variable name="p" select="translate(f:getparameter(replace($para,'^\$',''),$context),'&quot;','')"/>
						<xsl:variable name="q" select='translate($p,"&apos;","")'/>
						<xsl:value-of select="concat(substring-before($in,'${'),
								$q,
								f:minimizeParameter(substring($key,$paralength+1),$varmap,$context))"/>
					</xsl:when>
					<xsl:when test="contains($para,'$')"><!-- ${...$x...+...} -->
						<xsl:value-of select="concat(substring-before($in,'${'),
								'${',$para,'}',
								f:minimizeParameter(substring($key,$paralength+1),$varmap,$context))"/>				
					</xsl:when>
					<xsl:when test="contains($para,'$') and contains($para,'+')"><!-- ${...$x...+...} -->
						<xsl:value-of select="concat(substring-before($in,'${'),
								'${',f:noCurlies($para),'}',
								f:minimizeParameter(substring($key,$paralength+1),$varmap,$context))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="concat(substring-before($in,'${'),
								f:noCurlies($para),
								f:minimizeParameter(substring($key,$paralength+1),$varmap,$context))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="f:noCurlies($in)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:function name="f:minimizeParameter2" as="item()*"><!-- elaborate but wrap indices -->
		<xsl:param name="in"/><!--  as="item()" -->
		<xsl:param name="varmap" as="item()*"/>
		<xsl:param name="context" as="xs:string*"/>
		<xsl:variable name="h" as="item()*">
			<xsl:apply-templates select="$in" mode="genericHTML">
				<xsl:with-param name="toVariable" tunnel="yes" select="1"/>
				<xsl:with-param name="context" tunnel="yes" select="$context"/>
				<xsl:with-param name="varmap" tunnel="yes" select="$varmap"/>
			</xsl:apply-templates>
		</xsl:variable>
		<xsl:sequence select="$h/node()"/>		
<!--
		<xsl:variable name="h">
			<p>
				<xsl:analyze-string select="f:minimizeParameter($in,$varmap,$context)" regex="\$\{{[^\{{]*?\}}" flags="s">
					<xsl:matching-substring>
						<xsl:variable name="e" as="xs:string" 
							select="replace(normalize-space(substring(.,3,string-length(.)-3)),'#(.+?)#','\$$1')"/>
						<xsl:variable name="t" as="xs:string" select="f:stringEssence($e,$context,())"/>
						<xsl:choose>
							<xsl:when test="$t='NaN'">
								<xsl:value-of select="translate(normalize-space(substring(.,3,string-length(.)-3)),'$','')"/>
							</xsl:when>
							<xsl:otherwise>
								<xsl:value-of select="replace($t,'##suppress##.*##suppress##','','s')"/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:matching-substring>
					<xsl:non-matching-substring>
						<xsl:value-of select="replace(.,'#(.+?)#','\${$1}')"/>
					</xsl:non-matching-substring>
				</xsl:analyze-string>
			</p>
		</xsl:variable>
		<xsl:variable name="p" as="item()*">
			<xsl:apply-templates select="$h" mode="genericHTML">
				<xsl:with-param name="toVariable" tunnel="yes" select="-1"/>
				<xsl:with-param name="context" tunnel="yes" select="$context"/>
				<xsl:with-param name="varmap" tunnel="yes" select="()"/>
			</xsl:apply-templates>
		</xsl:variable>
		<xsl:sequence select="$p/node()"/>		
-->
	</xsl:function>
	<xsl:function name="f:minimizeParameter2_old" as="item()*"><!-- elaborate but wrap indices -->
		<xsl:param name="in" as="xs:string"/>
		<xsl:param name="varmap" as="item()*"/>
		<xsl:param name="context" as="xs:string*"/>
		<xsl:choose>
			<xsl:when test="contains($in,'${')">
				<xsl:variable name="key" select="substring-after($in,'${')"/>
				<xsl:variable name="paralength" select="f:findClosingCurly($key,0)"/>
				<xsl:if test="$paralength=0">
					<xsl:message terminate="yes" select="concat('ERROR: No closing } in {',$key)"/>
				</xsl:if>
				<xsl:variable name="para" select="normalize-space(substring($key,1,$paralength -1))"/>
				<xsl:value-of select="substring-before($in,'${')"/>
				<xsl:choose>
					<xsl:when test="count($varmap[@Name=replace($para,'^\$','')])=1">
						<xsl:element name="ph">
							<xsl:attribute name="class" select="concat('Index:',$varmap[@Name=replace($para,'^\$','')]/@brackets)"/>
							<xsl:value-of select="$varmap[@Name=$para]"/>
						</xsl:element>
					</xsl:when>
					<xsl:when test="matches($para,'^\$[a-z]$')"><!-- ${$x} but unknown x -->
						<xsl:element name="ph">
							<xsl:attribute name="class" select="'Index:yes'"/>
							<xsl:value-of select="substring($para,2)"/>
						</xsl:element>
					</xsl:when>
					<xsl:when test="$ParaMaps2/key('parameter',concat($context,':',replace($para,'^\$','')))">
						<xsl:variable name="p" select="translate(f:getparameter(replace($para,'^\$',''),$context),'&quot;','')"/>
						<xsl:value-of select='translate($p,"&apos;","")'/>
					</xsl:when>
					<xsl:when test="contains($para,'$') and contains($para,'+')"><!-- ${...$x...+...} -->
						<xsl:value-of select="concat('{',f:noCurlies($para),'}')"/>
					</xsl:when>
					<xsl:when test="matches($para,'^[a-z]$')">
						<xsl:element name="ph">
							<xsl:attribute name="class" select="'Index:yes'"/>
							<xsl:value-of select="$para"/>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="f:noCurlies($para)"/>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:copy-of select="f:minimizeParameter2_old(substring($key,$paralength+1),$varmap,$context)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="f:noCurlies($in)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:function name="f:minimizeParameter3" as="xs:string*"><!-- elaborate but decorate indices with #i# -->
		<xsl:param name="in" as="xs:string"/>
		<xsl:param name="varmap" as="item()*"/>
		<xsl:param name="context" as="xs:string*"/>
		<xsl:choose>
			<xsl:when test="contains($in,'${')">
				<xsl:variable name="key" select="substring-after($in,'${')"/>
				<xsl:variable name="paralength" select="f:findClosingCurly($key,0)"/>
				<xsl:if test="$paralength=0">
					<xsl:message terminate="yes" select="concat('ERROR: No closing } in {',$key)"/>
				</xsl:if>
				<xsl:variable name="para" select="normalize-space(substring($key,1,$paralength -1))"/>
				<xsl:value-of select="substring-before($in,'${')"/>
				<xsl:choose>
					<xsl:when test="count($varmap[@Name=replace($para,'^\$','')])=1">
						<xsl:value-of select="concat('#',$varmap[@Name=replace($para,'^\$','')],'#')"/>
					</xsl:when>
					<xsl:when test="matches($para,'\$[a-z]')"><!-- ${$x} but unknown x -->
						<xsl:value-of select="concat('#',substring($para,2),'#')"/>
					</xsl:when>
					<xsl:when test="$ParaMaps2/key('parameter',concat($context,':',replace($para,'^\$','')))">
						<xsl:variable name="p" select="translate(f:getparameter(replace($para,'^\$',''),$context),'&quot;','')"/>
						<xsl:value-of select='translate($p,"&apos;","")'/>
					</xsl:when>
					<xsl:when test="contains($para,'$') and contains($para,'+')"><!-- ${...$x...+...} -->
						<xsl:value-of select="concat('{',f:noCurlies($para),'}')"/>
					</xsl:when>
					<xsl:when test="matches($para,'^[a-z]$')">
						<xsl:element name="ph">
							<xsl:attribute name="class" select="'Index:yes'"/>
							<xsl:value-of select="$para"/>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="f:noCurlies($para)"/>
					</xsl:otherwise>
				</xsl:choose>
				<xsl:copy-of select="f:minimizeParameter3(substring($key,$paralength+1),$varmap,$context)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="f:noCurlies($in)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:function name="f:findClosingCurly" as="xs:integer">
		<xsl:param name="key" as="xs:string"/>
		<xsl:param name="sum" as="xs:integer"/>
		<xsl:variable name="quot" select="string-length(substring-before($key,'&quot;'))"/>
		<xsl:variable name="apos" select='string-length(substring-before($key,"&apos;"))'/>
		<xsl:variable name="curl" select="string-length(substring-before($key,'}'))"/>
		<xsl:choose>
			<xsl:when test="$curl &gt; 0 and ($quot = 0 or $quot &gt; $curl) and ($apos = 0 or $apos &gt; $curl)">
				<!-- no other char in curlies -->
				<xsl:value-of select="$sum+$curl+1"/>
			</xsl:when>
			<xsl:when test="$quot != 0 and ($apos = 0 or $apos &gt; $quot)">
				<!-- at least one quote before curly -->
				<xsl:variable name="rest" select="substring($key,$quot+2)"/>
				<xsl:variable name="quot2" select="string-length(substring-before($rest,'&quot;'))"/>
				<xsl:choose>
					<xsl:when test="$quot2 = 0"><xsl:value-of select="0"/></xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="f:findClosingCurly(substring($rest,$quot2+2),$sum+$quot+$quot2+2)"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$apos != 0 and ($quot = 0 or $quot &gt; $apos)">
				<!-- at least one apos before curly -->
				<xsl:variable name="rest" select="substring($key,$apos+2)"/>
				<xsl:variable name="apos2" select='string-length(substring-before($rest,"&apos;"))'/>
				<xsl:choose>
					<xsl:when test="$apos2 = 0"><xsl:value-of select="0"/></xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="f:findClosingCurly(substring($rest,$apos2+2),$sum+$apos+$apos2+2)"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="0"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:function name="f:noCurlies" as="xs:string">
		<xsl:param name="in" as="xs:string"/>
		<xsl:variable name="temp" select="replace(replace($in,'&quot;\{&quot;','\$curlyLeft'),'&quot;\}&quot;','\$curlyRight')"/>
		<xsl:value-of select='replace(replace($temp,"&apos;\{&apos;","\$curlyLeft"),"&apos;\}&apos;","\$curlyRight")'/>
	</xsl:function>
	<!-- conversion functions -->
	<xsl:function name="f:str2base" as="xs:decimal">
		<xsl:param name="in" as="xs:string"/>
		<xsl:param name="base" as="xs:integer"/>
		<xsl:variable name="h" as="xs:integer" select="string-length(substring-before('_0123456789ABCDEF',upper-case(substring($in,string-length($in)))))-1"/>
		<xsl:choose>
			<xsl:when test="string-length($in) &lt; 2">
				<xsl:sequence select="xs:decimal($h)"/>
			</xsl:when>
			<xsl:when test="matches($in,'^0+?.$')">
				<xsl:sequence select="xs:decimal($h)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="xs:decimal($h) + $base*f:str2base(replace(replace($in,'^0+',''),'.$',''),$base)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!--  -->
	<xsl:function name="f:str2dec__" as="xs:integer">
		<xsl:param name="in" as="xs:string"/>
		<xsl:sequence select="f:str2base($in,10)"/>
	</xsl:function>
	<!--	-->
	<!-- basic math functions -->
	<!-- Attention: xs:double is limited to 10 bit signed exponent (max = 1.7976931348623158e+308 ) -->
	<!--	-->
	<!-- Power -->
	<xsl:function name="f:power" as="xs:double">
		<xsl:param name="base" as="xs:double"/>
		<xsl:param name="exp" as="xs:integer"/>
		<xsl:sequence select="if ($exp lt 0) then f:powerh(1.0 div $base, -$exp) 
                else if ($exp eq 0) then 1e0 
                else f:powerh($base, $exp)"/>
	</xsl:function>
	<xsl:function name="f:powerh" as="xs:double">
		<xsl:param name="base" as="xs:double"/>
		<xsl:param name="exp" as="xs:integer"/><!-- 1,2,... -->
		<xsl:choose>
			<xsl:when test="$exp eq 1"><xsl:sequence select="$base"/></xsl:when>
			<xsl:when test="$exp eq 2"><xsl:sequence select="$base*$base"/></xsl:when>
			<xsl:when test="$exp eq 3"><xsl:sequence select="$base*$base*$base"/></xsl:when>
			<xsl:otherwise>
				<xsl:variable name="h" as="xs:double" select="f:powerh($base, xs:integer(floor($exp div 2)))"/>
				<xsl:sequence select="if ($exp mod 2 eq 0) then $h*$h else $base*$h*$h"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<xsl:function name="f:power2" as="xs:decimal">
		<xsl:param name="exp" as="xs:integer"/><!-- 1,2,... -->
		<xsl:choose>
			<xsl:when test="$exp lt 0"><xsl:sequence select="xs:decimal(1.0 div f:power2(-$exp))"/></xsl:when>
			<xsl:when test="$exp eq 0"><xsl:sequence select="1"/></xsl:when>
			<xsl:when test="$exp eq 1"><xsl:sequence select="2"/></xsl:when>
			<xsl:when test="$exp eq 2"><xsl:sequence select="4"/></xsl:when>
			<xsl:when test="$exp eq 3"><xsl:sequence select="8"/></xsl:when>
			<xsl:otherwise>
				<xsl:variable name="h" as="xs:decimal" select="f:power2(xs:integer(floor($exp div 2)))"/>
				<xsl:sequence select="if ($exp mod 2 eq 0) then $h*$h else 2*$h*$h"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- Sqrt -->
	<xsl:function name="f:sqrt" as="xs:double">
		<xsl:param name="number" as="xs:double"/>
		<xsl:variable name="try" select="if ($number lt 100.0) then 1.0
                                    else if ($number gt 100.0 and $number lt
                                             1000.0) then 10.0
                                    else if ($number gt 1000.0 and $number lt
                                             10000.0) then 31.0
                                    else 100.00" as="xs:decimal"/>
		<xsl:sequence select="if ($number ge 0) then f:sqrt($number,$try,1,20) 
                         else number('X')"/>
	</xsl:function>
	<xsl:function name="f:sqrt" as="xs:double">
		<xsl:param name="number" as="xs:double"/>
		<xsl:param name="try" as="xs:double"/>
		<xsl:param name="iter" as="xs:integer"/>
		<xsl:param name="maxiter" as="xs:integer"/>
		<xsl:variable name="result" select="$try * $try" as="xs:double"/>
		<xsl:sequence select="if ($result eq $number or $iter gt $maxiter) 
                          then $try 
                          else f:sqrt($number, ($try - (($result - $number) 
                                         div (2 * $try))), $iter + 1, $maxiter)"/>
	</xsl:function>
	<!-- Factorial -->
	<xsl:function name="f:factorial" as="xs:decimal">
		<xsl:param name="n" as="xs:integer"/>
		<xsl:sequence select="if ($n eq 0) then 1 else $n * f:factorial($n - 1)"/>
	</xsl:function>
	<!-- Prod-range -->
	<xsl:function name="f:prod-range" as="xs:decimal">
		<xsl:param name="from" as="xs:integer"/>
		<xsl:param name="to" as="xs:integer"/>
		<xsl:sequence select="if ($from ge $to) 
                          then $from 
                          else $from * f:prod-range($from + 1, $to)"/>
	</xsl:function>
	<!-- Log10 -->
	<xsl:function name="f:log10" as="xs:double">
		<xsl:param name="number" as="xs:double"/>
		<xsl:sequence select="if ($number le 0) then number('X') else f:log10($number,0)"/>
	</xsl:function>
	<xsl:function name="f:log10" as="xs:double">
		<xsl:param name="number" as="xs:double"/>
		<xsl:param name="n" as="xs:double"/>
		<xsl:sequence select="if ($number le 1) 
                          then f:log10($number * 10, $n - 1) 
                          else if($number gt 10) 
                          then f:log10($number div 10, $n + 1)
                          else if($number eq 10) 
                          then $n + 1
                          else $n + f:log10-util($number,0,0,2,38)"/>
	</xsl:function>
	<xsl:function name="f:log10-util" as="xs:double">
		<xsl:param name="number" as="xs:double"/>
		<xsl:param name="frac" as="xs:double"/>
		<xsl:param name="iter" as="xs:integer"/>
		<xsl:param name="divisor" as="xs:double"/>
		<xsl:param name="maxiter" as="xs:integer"/>
		<xsl:variable name="x" select="$number * $number"/>
		<xsl:sequence select="if ($iter ge $maxiter)
                          then round-half-to-even($frac,10)
                          else if ($x lt 10)
                          then f:log10-util($x,$frac,$iter + 1, 
                                               $divisor * 2, $maxiter)
                          else f:log10-util($x div 10,
                                               $frac + (1 div $divisor),
                                               $iter + 1, $divisor * 2,
                                               $maxiter)"/>
	</xsl:function>
	<!--	-->
	<!-- log for xs:decimal -->
	<xsl:function name="f:log" as="xs:decimal">
		<xsl:param name="number" as="xs:decimal"/>
		<xsl:param name="base" as="xs:decimal"/>
		<xsl:sequence select="f:logh($number,$base,$base*$base,0)"/>
	</xsl:function>
	<xsl:function name="f:logh" as="xs:decimal">
		<xsl:param name="number" as="xs:decimal"/>
		<xsl:param name="base" as="xs:decimal"/>
		<xsl:param name="base2" as="xs:decimal"/>
		<xsl:param name="n" as="xs:decimal"/>		
		<xsl:sequence select="if ($number lt $base) 
                          then $n
                          else if($number lt $base2) 
                          then $n + 1
                          else if($number eq $base2) 
                          then $n + 2
                          else f:logh($number idiv $base2,$base,$base2,$n + 2)"/>		
	</xsl:function>
	<!--	-->
	<!-- the substring-before() for duadic - -->
	<xsl:function name="f:beforeLastMinus" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="result" as="xs:string"/>
		<xsl:choose>
			<xsl:when test="not(matches($input,'[\d\w]+\s*-'))">
				<xsl:value-of select="$result"/>
			</xsl:when>
			<xsl:when test="string-length($result)=0">
				<xsl:value-of select="f:beforeLastMinus(replace($input,'^.*[\d\w]+\s*-',''),replace($input,'^(.*[\d\w]+\s*)-.*$','$1'))"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="f:beforeLastMinus(replace($input,'^.*[\d\w]+\s*-',''),concat($result,'-',replace($input,'^(.*[\d\w]+\s*)-.*$','$1')))"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!--	-->
	<!-- the solver function for () + - * / mod div ^ -->
	<xsl:function name="f:evaluate" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:value-of select="f:evaluate($input,'0')"/>
	</xsl:function>
	<xsl:function name="f:evaluate" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:choose>
			<!-- nothing becomes 0 -->
			<xsl:when test="$input=' '">
				<xsl:value-of select="number(0)"/>
			</xsl:when>
			<!-- prio 1: ( ) -->
			<xsl:when test="contains($input,')')">
				<xsl:variable name="bracket" select="replace(substring-before($input,')'),'^.*\(','')"/>
				<xsl:variable name="prebracket" select="substring($input,1,string-length(substring-before($input,')'))-1-string-length($bracket))"/>
				<xsl:choose>
					<xsl:when test="matches($prebracket,'dec\d*$')">
						<xsl:variable name="s" select="string(xs:integer(f:evaluate($bracket,$context)))" as="xs:string"/>
						<xsl:variable name="p" select="for $i in string-length($s) +1 to xs:integer(replace($prebracket,'.*dec(\d*)$','0$1')) return '0'" as="xs:string*"/>
						<xsl:value-of select="concat(replace($prebracket,'dec\d*$',''),string-join($p,''),$s,substring-after($input,')'))"/>
					</xsl:when>
					<xsl:when test="matches($prebracket,'hex\d*$')">
						<xsl:variable name="s" select="f:decimal-to-hex(number(f:evaluate($bracket,$context)))" as="xs:string"/>
						<xsl:variable name="p" select="for $i in string-length($s) +1 to xs:integer(replace($prebracket,'.*hex(\d*)$','0$1')) return '0'" as="xs:string*"/>
						<xsl:value-of select="concat(replace($prebracket,'hex\d*$',''),string-join($p,''),$s,substring-after($input,')'))"/>
					</xsl:when>
					<xsl:when test="matches($prebracket,'bin\d*$')">
						<xsl:variable name="s" select="f:decimal-to-bin(number(f:evaluate($bracket,$context)))" as="xs:string"/>
						<xsl:variable name="p" select="for $i in string-length($s) +1 to xs:integer(replace($prebracket,'.*bin(\d*)$','0$1')) return '0'" as="xs:string*"/>
						<xsl:value-of select="concat(replace($prebracket,'bin\d*$',''),string-join($p,''),$s,substring-after($input,')'))"/>
					</xsl:when>
					<xsl:when test="matches($prebracket,'eng$')">
						<xsl:variable name="val" select="number(f:evaluate($bracket,$context))" as="xs:double"/>
						<xsl:variable name="p" as="xs:string*">
							<xsl:choose>
								<xsl:when test="$val &gt;= 1073741824">
									<xsl:value-of select="floor($val div 10737418.24) div 100"/>
									<xsl:text>GB</xsl:text>
								</xsl:when>
								<xsl:when test="$val &gt;= 1048576">
									<xsl:value-of select="floor($val div 10485.76) div 100"/>
									<xsl:text>MB</xsl:text>
								</xsl:when>
								<xsl:when test="$val &gt;= 1024">
									<xsl:value-of select="floor($val div 10.24) div 100"/>
									<xsl:text>KB</xsl:text>
								</xsl:when>
								<xsl:otherwise>
									<xsl:value-of select="$val"/>
									<xsl:text>B</xsl:text>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:variable>						
						<xsl:value-of select="concat(replace($prebracket,'eng$',''),string-join($p,''),substring-after($input,')'))"/>
					</xsl:when>
					<xsl:when test="matches($prebracket,'pow\d+$')">
						<xsl:variable name="e" select="xs:integer(f:evaluate($bracket,$context))" as="xs:integer"/>
						<xsl:variable name="b" select="number(replace($prebracket,'.*pow(\d+)$','$1'))" as="xs:double"/>
						<xsl:value-of select="number(f:evaluate(concat(replace($prebracket,'pow\d+$',''),string(f:power($b,$e)),substring-after($input,')')),$context))"/>
					</xsl:when>
					<xsl:when test="matches($prebracket,'min$')">
						<xsl:variable name="vals" select="tokenize($bracket,',')"/>
						<xsl:for-each select="$vals">
							<xsl:sort select="." data-type="number" order="ascending"/>
							<xsl:if test="position()=1">
								<xsl:value-of select="f:evaluate(concat(replace($prebracket,'min$',''),.,substring-after($input,')')),$context)"/>
							</xsl:if>
						</xsl:for-each>
					</xsl:when>
					<xsl:when test="matches($prebracket,'max$')">
						<xsl:variable name="vals" select="tokenize($bracket,',')"/>
						<xsl:for-each select="$vals">
							<xsl:sort select="." data-type="number" order="descending"/>
							<xsl:if test="position()=1">
								<xsl:value-of select="f:evaluate(concat(replace($prebracket,'max$',''),.,substring-after($input,')')),$context)"/>
							</xsl:if>
						</xsl:for-each>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="number(f:evaluate(concat($prebracket,f:evaluate($bracket,$context),substring-after($input,')')),$context))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- least binding: + - -->
			<xsl:when test="contains($input,'+') or matches($input,'[\d\w]+\s*-')">
				<xsl:variable name="plus" select="string-length(substring-before($input,'+'))"/>
				<xsl:variable name="minus" select="string-length(f:beforeLastMinus($input,''))"/>		
				<xsl:choose>
					<xsl:when test="$plus &lt; $minus"><!-- no + or no + after - -->
						<xsl:value-of select="number(f:evaluate(substring($input,1,$minus),$context)) - number(f:evaluate(substring($input,$minus+2),$context))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="number(f:evaluate(substring($input,1,$plus),$context)) + number(f:evaluate(substring($input,$plus+2),$context))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- highest binding: * / mod div -->
			<xsl:when test="contains($input,'*') or contains($input,'/') or contains($input,' div ') or contains($input,'mod')">
				<xsl:variable name="mul" select="string-length(substring-before($input,'*'))"/>
				<xsl:variable name="div" select="string-length(substring-before($input,'/'))"/>
				<xsl:variable name="idiv" select="string-length(substring-before($input,' div '))"/>
				<xsl:variable name="mod" select="string-length(substring-before($input,' mod '))"/>
				<xsl:choose>
					<xsl:when test="$mul &gt; $div and $mul &gt; $idiv and $mul &gt; $mod">
						<xsl:value-of select="number(f:evaluate(substring-before($input,'*'),$context)) * number(f:evaluate(substring-after($input,'*'),$context))"/>
					</xsl:when>
					<xsl:when test="$div &gt; $mul and $div &gt; $idiv and $div &gt; $mod">
						<xsl:value-of select="number(f:evaluate(substring-before($input,'/'),$context)) div  number(f:evaluate(substring-after($input,'/'),$context))"/>
					</xsl:when>
					<xsl:when test="$idiv &gt; $mul and $idiv &gt; $div and $idiv &gt; $mod">
						<xsl:value-of select="floor(number(f:evaluate(substring-before($input,' div '),$context)) div  number(f:evaluate(substring-after($input,' div '),$context)))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="number(f:evaluate(substring-before($input,' mod '),$context)) mod number(f:evaluate(substring-after($input,' mod '),$context))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- highest binding: ^ -->
			<xsl:when test="contains($input,'^')">
				<xsl:variable name="b" select="number(f:evaluate(substring-before($input,'^'),$context))"/>
				<xsl:variable name="e" select="number(f:evaluate(substring-after($input,'^'),$context))"/>
				<xsl:choose>
					<xsl:when test="$b = 1 or $e = 0">
						<xsl:value-of select="1"/>
					</xsl:when>
					<xsl:when test="$b = 0">
						<xsl:value-of select="0"/>
					</xsl:when>
					<xsl:when test="$e = 1">
						<xsl:value-of select="$b"/>
					</xsl:when>
					<xsl:when test="$b castable as xs:double and $e castable as xs:integer">
						<xsl:value-of select="f:power($b, xs:integer($e))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:message terminate="yes">ERROR: Not a valid numeric expression <xsl:value-of select="$input"/></xsl:message>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- variables $ -->
			<xsl:when test="starts-with(normalize-space($input),'$')">
				<xsl:value-of select="f:evaluate(normalize-space(f:getparameter(substring-after($input,'$'),$context)),$context)"/>
			</xsl:when>
			<!-- literals -->
			<xsl:when test="starts-with(upper-case(normalize-space($input)),'0B')">
				<xsl:value-of select="f:str2base(substring(normalize-space($input),3),2)"/>
			</xsl:when>
			<xsl:when test="starts-with(upper-case(normalize-space($input)),'0X')">
				<xsl:value-of select="f:str2base(substring(normalize-space($input),3),16)"/>
			</xsl:when>
			<xsl:when test="$input castable as xs:double">
				<xsl:value-of select="number($input)"/>
			</xsl:when>
			<xsl:when test="$context='0'">
				<xsl:value-of select="number($input)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:message terminate="yes">ERROR: Expression is not a valid number - "<xsl:sequence select="$input"/>"</xsl:message>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- -->
	<!-- essence file key -->
	<xsl:function name="f:makeKey" as="xs:string">
		<xsl:param name="vlnv" as="item()*"/>
		<xsl:if test="count($vlnv)=0"><xsl:message terminate="yes">ERROR: No VLNV given in input data</xsl:message></xsl:if>
		<xsl:value-of select="string-join(($vlnv[1]//Vendor,$vlnv[1]//Library,$vlnv[1]//Name,$vlnv[1]//Version),':')"/>
	</xsl:function>
	<!-- -->
	<!-- the solver function for () ! + -  * / % ^  < <= == =~ !~ != >= >  TRUE FALSE 0x0 0o0 0b0 $v "x" 'x' -->
	<xsl:function name="f:booleanEssence" as="xs:integer">
		<xsl:param name="input" as="xs:string"/>
		<xsl:sequence select="f:booleanEssence($input,'0')"/>
	</xsl:function>
	<xsl:function name="f:booleanEssence" as="xs:integer">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:sequence select="xs:integer(f:numEssence(f:parseEssence($input),$context))"/>
	</xsl:function>
	<!-- -->
	<!-- the same solver, but returns false (0) if any unresolved variable is found -->
	<xsl:function name="f:booleanConstEssence" as="xs:integer">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="keep" as="xs:string*"/>
		<xsl:sequence select="f:booleanConstEssence($input,$keep,'0')"/>
	</xsl:function>
	<xsl:function name="f:booleanConstEssence" as="xs:integer">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="keep" as="xs:string*"/>
		<xsl:param name="context" as="xs:string"/>
		<!-- do the constant folding to remove redundant variable terms -->
		<xsl:sequence select="f:constantTrue(f:pruneEssence(f:parseEssence($input),$context,(),1))"/><!-- 0 to disable "no_internal" -->
	</xsl:function>
	<xsl:function name="f:constantTrue" as="xs:integer">
		<xsl:param name="mapped" as="item()*"/>
		<xsl:choose>
			<xsl:when test="$mapped[1]/@kind='var'">0</xsl:when>
			<xsl:when test="count($mapped//*[@kind='var']) &gt; 0">0</xsl:when>
			<xsl:otherwise>
				<xsl:sequence select="xs:integer(f:numEssence($mapped,'0'))"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- -->
	<!-- the solver function for () ! + -  * / % ^  0x0 0o0 0b0 $v  -->
	<xsl:function name="f:integerEssence" as="xs:decimal">
		<xsl:param name="input" as="xs:string"/>
		<xsl:sequence select="f:integerEssence($input,'0')"/>
	</xsl:function>
	<xsl:function name="f:integerEssence" as="xs:decimal">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:sequence select="f:numEssence(f:parseEssence($input),$context)"/>
	</xsl:function>
	<xsl:function name="f:integerEssence" as="xs:decimal">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:param name="varmap" as="item()*"/>
		<xsl:sequence select="f:numEssence(f:pruneEssence(f:parseEssence($input),$context,$varmap,0),$context)"/>
	</xsl:function>
	<!-- -->
	<!-- the solver function for () + $v "x" 'x' -->
	<xsl:function name="f:stringEssence" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:value-of select="f:stringEssence($input,'0')"/>
	</xsl:function>
	<xsl:function name="f:stringEssence" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:value-of select="f:textEssence(f:parseEssence($input),$context)"/>
	</xsl:function>
	<xsl:function name="f:stringEssence" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:param name="varmap" as="item()*"/>
		<xsl:value-of select="f:textEssence(f:pruneEssence(f:parseEssence($input),$context,$varmap,0),$context)"/>
	</xsl:function>
	<!-- -->
	<!-- the same solver, but replaces variable passed in $keep by their name -->
	<xsl:function name="f:stringKeepEssence" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="keep" as="xs:string*"/>
		<xsl:value-of select="f:stringKeepEssence($input,$keep,'0')"/>
	</xsl:function>
	<xsl:function name="f:stringKeepEssence" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="keep" as="xs:string*"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:variable name="varmap" as="item()*">
			<xsl:for-each select="$keep">
				<index>
					<xsl:attribute name="Name" select="."/>
					<xsl:value-of select="."/>
				</index>
			</xsl:for-each>
		</xsl:variable>
		<xsl:value-of select="f:textEssence(f:pruneEssence(f:parseEssence($input),$context,$varmap,0),$context)"/>
	</xsl:function>
	<!--		-->
	<!--	====================================================================	-->
	<!--	========	Essence Expression Handling    ================================== 	-->
	<!--		-->
	<!--	Translate an Essence element (like Hidden) into a syntax tree -->
	<xsl:function name="f:parseEssence" as="item()*">
		<xsl:param name="in" as="xs:string"/>
		<xsl:variable name="consts" as="item()*">
			<xsl:for-each select="f:extractQuoted($in,(''))">
				<op kind="const" type="string" prio="8">
					<xsl:attribute name="pos" select="position()"/>
					<xsl:value-of select="."/>
				</op>
			</xsl:for-each>
		</xsl:variable>
		<xsl:variable name="patched" select="f:patchQuoted($in,$consts)"/>
		<xsl:copy-of select="f:toTreeEssence($patched,$consts)"/>
	</xsl:function>
	<!--	Extract all quoted substrings from an Essence expression -->
	<xsl:function name="f:extractQuoted" as="xs:string*">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="consts" as="xs:string*"/>
		<xsl:variable name="double" select="string-length(substring-before(concat($input,'&quot;'),'&quot;'))"/>
		<xsl:variable name="single" select='string-length(substring-before(concat($input,"&apos;"),"&apos;"))'/>
		<xsl:choose>
			<xsl:when test="$double &lt; $single">
				<xsl:variable name="s" select="substring-after($input,'&quot;')"/>
				<xsl:choose>
					<xsl:when test="$double=0 and string-length($s)=0"><!-- just a single " -->
						<xsl:copy-of select="f:extractQuoted(substring-after($s,'&quot;'),($consts,'&quot;'))"/>
					</xsl:when>
					<xsl:when test="starts-with($s,'&quot;')">
						<xsl:copy-of select="f:extractQuoted(substring-after($s,'&quot;'),($consts))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy-of select="f:extractQuoted(substring-after($s,'&quot;'),($consts,substring-before($s,'&quot;')))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$double &gt; $single">
				<xsl:variable name="s" select='substring-after($input,"&apos;")'/>
				<xsl:choose>
					<xsl:when test="$single=0 and string-length($s)=0"><!-- just a single ' -->
						<xsl:copy-of select='f:extractQuoted(substring-after($s,"&apos;"),($consts,"&apos;"))'/>
					</xsl:when>
					<xsl:when test='starts-with($s,"&apos;")'>
						<xsl:copy-of select='f:extractQuoted(substring-after($s,"&apos;"),($consts))'/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy-of select='f:extractQuoted(substring-after($s,"&apos;"),($consts,substring-before($s,"&apos;")))'/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:copy-of select="$consts"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!--	Replace all quoted substrings in an Essence expression by $$n with n being the index in $consts -->
	<xsl:function name="f:patchQuoted" as="xs:string">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="consts" as="item()*"/>
		<xsl:variable name="double" select="string-length(substring-before(concat($input,'&quot;'),'&quot;'))"/>
		<xsl:variable name="single" select='string-length(substring-before(concat($input,"&apos;"),"&apos;"))'/>
		<xsl:choose>
			<xsl:when test="$double &lt; $single">
				<xsl:variable name="s" select="substring-after($input,'&quot;')"/>
				<xsl:choose>
					<xsl:when test="$double=0 and string-length($s)=0"><!-- just a single " -->
						<xsl:value-of select="concat('$$',$consts[text()='&quot;'][1]/@pos)"/>
					</xsl:when>
					<xsl:when test="starts-with($s,'&quot;')">
						<xsl:value-of select="concat(substring($input,1,$double),'$$1',f:patchQuoted(substring-after($s,'&quot;'),$consts))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="concat(substring($input,1,$double),'$$',$consts[text()=substring-before($s,'&quot;')][1]/@pos,
									f:patchQuoted(substring-after($s,'&quot;'),$consts))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$double &gt; $single">
				<xsl:variable name="s" select='substring-after($input,"&apos;")'/>
				<xsl:choose>
					<xsl:when test="$single=0 and string-length($s)=0"><!-- just a single ' -->
						<xsl:value-of select='concat("$$",$consts[text()="&apos;"][1]/@pos)'/>
					</xsl:when>
					<xsl:when test='starts-with($s,"&apos;")'>
						<xsl:value-of select='concat(substring($input,1,$single),"$$1",f:patchQuoted(substring-after($s,"&apos;"),$consts))'/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select='concat(substring($input,1,$single),"$$",$consts[text()=substring-before($s,"&apos;")][1]/@pos,
									f:patchQuoted(substring-after($s,"&apos;"),$consts))'/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="$input"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- the recursive parser function for () ! + -  * / % ^  < <= == =~ !~ != >= >  TRUE FALSE 0x0 0o0 0b0 $v $$c -->
	<xsl:function name="f:toTreeEssence" as="item()*">
		<xsl:param name="input" as="xs:string"/>
		<xsl:param name="consts" as="item()*"/>
		<xsl:choose>
			<xsl:when test="matches($input,'^\s*\$curlyLeft\s*$')">
				<op kind="const" type="string" prio="8">
					<xsl:value-of select="'{'"/>
				</op>
			</xsl:when>
			<xsl:when test="matches($input,'^\s*\$curlyRight\s*$')">
				<op kind="const" type="string" prio="8">
					<xsl:value-of select="'}'"/>
				</op>
			</xsl:when>
			<xsl:when test="matches($input,'^\s*true\s*$','i')">
				<op kind="const" type="bool" prio="8">1</op>
			</xsl:when>
			<xsl:when test="matches($input,'^\s*false\s*$','i')">
				<op kind="const" type="bool" prio="8">0</op>
			</xsl:when>
			<!-- prio 1: ( ) -->
			<xsl:when test="contains($input,')')">
				<xsl:variable name="s" select="substring-before($input,')')"/>
				<xsl:variable name="bracket" select="replace($s,'^.*\(','')"/><!-- greedy required here! -->
				<xsl:variable name="brack" select="string-length($s) +1"/><!-- after first ) -->
				<xsl:variable name="lbrack" select="replace($s,'\s*\([^\(]*$','')"/>
				<xsl:variable name="rbrack" select="substring($input,$brack + 1,string-length($input)-$brack)"/>
				<xsl:choose>
					<xsl:when test="string-length($lbrack)=0">
						<xsl:variable name="subtree" select="f:toTreeEssence($bracket,$consts)"/>
						<xsl:copy-of select="f:toTreeEssence(concat(concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>
					</xsl:when>
					<xsl:when test="ends-with($lbrack,'min')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="int" prio="8">
								<op kind="const" type="string" prio="8">min</op>
								<xsl:for-each select="tokenize($bracket,',')"><!--TODO string parameters lengthening $const -->
									<xsl:copy-of select="f:toTreeEssence(.,$consts)"/>
								</xsl:for-each>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'min$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="ends-with($lbrack,'max')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="int" prio="8">
								<op kind="const" type="string" prio="8">max</op>
								<xsl:for-each select="tokenize($bracket,',')"><!--TODO string parameters lengthening $const -->
									<xsl:copy-of select="f:toTreeEssence(.,$consts)"/>
								</xsl:for-each>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'max$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="ends-with($lbrack,'rshift')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="int" prio="8">
								<op kind="const" type="string" prio="8">rshift</op>
								<xsl:for-each select="tokenize($bracket,',')"><!--TODO string parameters lengthening $const -->
									<xsl:copy-of select="f:toTreeEssence(.,$consts)"/>
								</xsl:for-each>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'rshift$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="ends-with($lbrack,'lshift')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="int" prio="8">
								<op kind="const" type="string" prio="8">lshift</op>
								<xsl:for-each select="tokenize($bracket,',')"><!--TODO string parameters lengthening $const -->
									<xsl:copy-of select="f:toTreeEssence(.,$consts)"/>
								</xsl:for-each>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'lshift$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="ends-with($lbrack,'log')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="int" prio="8">
								<op kind="const" type="string" prio="8">log</op>
								<xsl:for-each select="tokenize($bracket,',')"><!--TODO string parameters lengthening $const -->
									<xsl:copy-of select="f:toTreeEssence(.,$consts)"/>
								</xsl:for-each>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'log$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="matches($lbrack,'dec\d*$')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="string" prio="8">
								<op kind="const" type="string" prio="8"><xsl:value-of select="'dec'"/></op>
								<op kind="const" type="int" prio="8">
									<xsl:choose>
										<xsl:when test="ends-with($lbrack,'dec')"><xsl:value-of select="1"/></xsl:when>
										<xsl:otherwise><xsl:value-of select="substring-after($lbrack,'dec')"/></xsl:otherwise>
									</xsl:choose>
								</op>
								<xsl:copy-of select="f:toTreeEssence($bracket,$consts)"/>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'dec\d*$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="matches($lbrack,'hex\d*$')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="string" prio="8">
								<op kind="const" type="string" prio="8"><xsl:value-of select="'hex'"/></op>
								<op kind="const" type="int" prio="8">
									<xsl:choose>
										<xsl:when test="ends-with($lbrack,'hex')"><xsl:value-of select="1"/></xsl:when>
										<xsl:otherwise><xsl:value-of select="substring-after($lbrack,'hex')"/></xsl:otherwise>
									</xsl:choose>
								</op>
								<xsl:copy-of select="f:toTreeEssence($bracket,$consts)"/>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'hex\d*$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="matches($lbrack,'bin\d*$')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="string" prio="8">
								<op kind="const" type="string" prio="8"><xsl:value-of select="'bin'"/></op>
								<op kind="const" type="int" prio="8">
									<xsl:choose>
										<xsl:when test="ends-with($lbrack,'bin')"><xsl:value-of select="1"/></xsl:when>
										<xsl:otherwise><xsl:value-of select="substring-after($lbrack,'bin')"/></xsl:otherwise>
									</xsl:choose>
								</op>
								<xsl:copy-of select="f:toTreeEssence($bracket,$consts)"/>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'bin\d*$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="matches($lbrack,'eng$')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="string" prio="8">
								<op kind="const" type="string" prio="8"><xsl:value-of select="'eng'"/></op>
								<xsl:copy-of select="f:toTreeEssence($bracket,$consts)"/>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'eng$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="ends-with($lbrack,'list')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="int" prio="8">
								<op kind="const" type="string" prio="8">list</op>
								<xsl:for-each select="tokenize($bracket,',')"><!--TODO string parameters lengthening $const -->
									<xsl:copy-of select="f:toTreeEssence(.,$consts)"/>
								</xsl:for-each>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'list$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:when test="ends-with($lbrack,'pos')">
						<xsl:variable name="subtree" as="item()">
							<op kind="func" type="int" prio="8">
								<op kind="const" type="string" prio="8">pos</op>
								<xsl:for-each select="tokenize($bracket,',')"><!--TODO string parameters lengthening $const -->
									<xsl:copy-of select="f:toTreeEssence(.,$consts)"/>
								</xsl:for-each>
							</op>
						</xsl:variable>
						<xsl:copy-of select="f:toTreeEssence(concat(replace($lbrack,'pos$',''),concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>						
					</xsl:when>
					<xsl:otherwise>
						<xsl:variable name="subtree" select="f:toTreeEssence($bracket,$consts)"/>
						<xsl:copy-of select="f:toTreeEssence(concat($lbrack,concat('$$',string(count($consts)+1)),$rbrack),($consts,$subtree))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- least binding: & | ^ -->
			<xsl:when test="contains($input,'|') or contains($input,'&amp;') or contains($input,'^')">
				<xsl:variable name="orr" select="replace($input,'^.*\|+','')"/>
				<xsl:variable name="or" select="string-length($orr)"/><!-- after last | -->
				<xsl:variable name="andr" select="replace($input,'^.*&amp;+','')"/>
				<xsl:variable name="and" select="string-length($andr)"/><!-- after last & -->
				<xsl:variable name="xorr" select="replace($input,'^.*\^','')"/>
				<xsl:variable name="xor" select="string-length($xorr)"/><!-- after last ^ -->
				<xsl:choose>
					<xsl:when test="$and &lt; $or and $and &lt; $xor">
						<xsl:variable name="andl" select="replace(substring($input,1,string-length($input)-$and),'&amp;+$','')"/><!-- before last & -->
						<op kind="and" type="bool" prio="1">
							<xsl:copy-of select="f:toTreeEssence($andl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($andr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$or &lt; $and and $or &lt; $xor">
						<xsl:variable name="orl" select="replace(substring($input,1,string-length($input)-$or),'\|+$','')"/><!-- before last | -->
						<op kind="or" type="bool" prio="1">
							<xsl:copy-of select="f:toTreeEssence($orl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($orr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$xor &lt; $and and $xor &lt; $or">
						<xsl:variable name="xorl" select="substring($input,1,string-length($input)-$xor - 1)"/><!-- before last ^ -->
						<xsl:variable name="right" select="f:toTreeEssence($xorr,$consts)"/>
						<xsl:variable name="left" select="f:toTreeEssence($xorl,$consts)"/>
						<xsl:choose>
							<xsl:when test="$right/@type != 'bool' or $left/@type != 'bool'"><!-- make this an exponent -->
								<xsl:copy-of select="f:toTreeEssence(concat($xorl,'%%',$xorr),$consts)"/>
							</xsl:when>
							<xsl:otherwise>
								<op kind="xor" type="bool" prio="1">
									<xsl:copy-of select="$left"/>
									<xsl:copy-of select="$right"/>
								</op>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:when>
					<xsl:otherwise>
						<xsl:message terminate="yes">ERROR: Parsing error in &quot;<xsl:value-of select="$input"/>&quot; !</xsl:message>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- comparison operators -->
			<xsl:when test="contains($input,'=') or contains($input,'&lt;') or contains($input,'&gt;') or contains($input,'~')">
				<xsl:variable name="ltr" select="replace($input,'^.*&lt;','')"/>
				<xsl:variable name="lt" select="string-length($ltr)"/>
				<xsl:variable name="gtr" select="replace($input,'^.*&gt;','')"/>
				<xsl:variable name="gt" select="string-length($gtr)"/>
				<xsl:variable name="eqr" select="replace($input,'^.*==','')"/>
				<xsl:variable name="eq" select="string-length($eqr)"/>
				<xsl:variable name="ler" select="replace($input,'^.*&lt;=','')"/>
				<xsl:variable name="le" select="string-length($ler)"/>
				<xsl:variable name="ger" select="replace($input,'^.*&gt;=','')"/>
				<xsl:variable name="ge" select="string-length($ger)"/>
				<xsl:variable name="ner" select="replace($input,'^.*!=','')"/>
				<xsl:variable name="ne" select="string-length($ner)"/>
				<xsl:variable name="mar" select="replace($input,'^.*=~','')"/>
				<xsl:variable name="ma" select="string-length($mar)"/>
				<xsl:variable name="nmr" select="replace($input,'^.*!~','')"/>
				<xsl:variable name="nm" select="string-length($nmr)"/>
				<xsl:choose>
					<xsl:when test="$ne &lt; $lt and $ne &lt; $gt and $ne &lt; $eq and $ne &lt; $le and $ne &lt; $ge and $ne &lt; $ma and $ne &lt; $nm">
						<xsl:variable name="nel" select="substring($input,1,string-length($input)-$ne - 2)"/><!-- before last != -->
						<op kind="ne" type="bool" prio="2">
							<xsl:copy-of select="f:toTreeEssence($nel,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($ner,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$ge &lt; $lt and $ge &lt; $gt and $ge &lt; $eq and $ge &lt; $le and $ge &lt; $ne and $ge &lt; $ma and $ge &lt; $nm">
						<xsl:variable name="gel" select="substring($input,1,string-length($input)-$ge - 2)"/><!-- before last >= -->
						<op kind="ge" type="bool" prio="2">
							<xsl:copy-of select="f:toTreeEssence($gel,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($ger,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$le &lt; $lt and $le &lt; $gt and $le &lt; $eq and $le &lt; $ge and $le &lt; $ne and $le &lt; $ma and $le &lt; $nm">
						<xsl:variable name="lel" select="substring($input,1,string-length($input)-$le - 2)"/><!-- before last <= -->
						<op kind="le" type="bool" prio="2">
							<xsl:copy-of select="f:toTreeEssence($lel,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($ler,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$eq &lt; $lt and $eq &lt; $gt and $eq &lt; $le and $eq &lt; $ge and $eq &lt; $ne and $eq &lt; $ma and $eq &lt; $nm">
						<xsl:variable name="eql" select="substring($input,1,string-length($input)-$eq - 2)"/><!-- before last == -->
						<op kind="eq" type="bool" prio="2">
							<xsl:copy-of select="f:toTreeEssence($eql,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($eqr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$gt &lt; $lt and $gt &lt; $eq and $gt &lt; $le and $gt &lt; $ge and $gt &lt; $ne and $gt &lt; $ma and $gt &lt; $nm">
						<xsl:variable name="gtl" select="substring($input,1,string-length($input)-$gt - 1)"/><!-- before last > -->
						<op kind="gt" type="bool" prio="2">
							<xsl:copy-of select="f:toTreeEssence($gtl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($gtr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$lt &lt; $gt and $lt &lt; $eq and $lt &lt; $le and $lt &lt; $ge and $lt &lt; $ne and $lt &lt; $ma and $lt &lt; $nm">
						<xsl:variable name="ltl" select="substring($input,1,string-length($input)-$lt - 1)"/><!-- before last < -->
						<op kind="lt" type="bool" prio="2">
							<xsl:copy-of select="f:toTreeEssence($ltl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($ltr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$nm &lt; $lt and $nm &lt; $gt and $nm &lt; $eq and $nm &lt; $le and $nm &lt; $ge and $nm &lt; $ne and $nm &lt; $ma">
						<xsl:variable name="nml" select="substring($input,1,string-length($input)-$nm - 2)"/><!-- before last !~ -->
						<op kind="nm" type="bool" prio="2">
							<xsl:copy-of select="f:toTreeEssence($nml,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($nmr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$ma &lt; $lt and $ma &lt; $gt and $ma &lt; $eq and $ma &lt; $le and $ma &lt; $ge and $ma &lt; $ne and $ma &lt; $nm">
						<xsl:variable name="mal" select="substring($input,1,string-length($input)-$ma - 2)"/><!-- before last =~ -->
						<op kind="ma" type="bool" prio="2">
							<xsl:copy-of select="f:toTreeEssence($mal,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($mar,$consts)"/>
						</op>
					</xsl:when>
					<xsl:otherwise>
						<xsl:message terminate="yes">ERROR: Parsing error in &quot;<xsl:value-of select="$input"/>&quot; !</xsl:message>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- add/sub: + - -->
			<xsl:when test="contains($input,'+') or contains($input,'-')">
				<xsl:variable name="addr" select="replace($input,'^.*\+','')"/>
				<xsl:variable name="subr" select="replace($input,'^.*-','')"/>
				<xsl:variable name="add" select="string-length($addr)"/><!-- after last + -->
				<xsl:variable name="sub" select="string-length($subr)"/><!-- after last - -->
				<xsl:variable name="addl" select="substring($input,1,string-length($input)-$add - 1)"/><!-- before last + -->
				<xsl:variable name="subl" select="substring($input,1,string-length($input)-$sub - 1)"/><!-- before last + -->
				<xsl:choose>
					<xsl:when test="starts-with(normalize-space($input),'+')">
						<xsl:copy-of select="f:toTreeEssence(substring-after($input,'+'),$consts)"/>
					</xsl:when>
					<xsl:when test="starts-with(normalize-space($input),'-')">
						<xsl:copy-of select="f:toTreeEssence(concat('§',substring-after($input,'-')),$consts)"/>
					</xsl:when>					
					<xsl:when test="$add &lt; $sub and ends-with($addl,'-')">
						<xsl:variable name="left" select="f:toTreeEssence($subl,$consts)"/>
						<xsl:variable name="right" select="f:toTreeEssence($addr,$consts)"/>
						<op kind="sub" prio="3">
							<xsl:if test="$left[1]/@type='int' and $right[1]/@type='int'">
								<xsl:attribute name="type" select="'int'"/>
							</xsl:if>
							<xsl:copy-of select="$left"/>
							<xsl:copy-of select="$right"/>
						</op>
					</xsl:when>
					<xsl:when test="$add &lt; $sub">
						<xsl:variable name="left" select="f:toTreeEssence(replace($addl,'\+\s*$',''),$consts)"/>
						<xsl:variable name="right" select="f:toTreeEssence($addr,$consts)"/>
						<xsl:choose>
							<xsl:when test="$left[1]/@kind='cat' or $right[1]/@kind='cat'">
								<op kind="cat" type="string" prio="3">
									<xsl:copy-of select="$left"/>
									<xsl:copy-of select="$right"/>
								</op>
							</xsl:when>
							<xsl:when test="($left[1]/@type='string' and $left[1]/text()!='#') or ($right[1]/@type='string' and $right[1]/text()!='#')">
								<op kind="cat" type="string" prio="3">
									<xsl:copy-of select="$left"/>
									<xsl:copy-of select="$right"/>
								</op>
							</xsl:when>
							<xsl:when test="$left[1]/@kind='const' and string-length($left[1]/text())=0">
								<xsl:copy-of select="$right"/>
							</xsl:when>
							<xsl:when test="$right[1]/@kind='const' and string-length($right[1]/text())=0">
								<xsl:copy-of select="$left"/>
							</xsl:when>
							<xsl:otherwise>
								<op kind="add" prio="3">
									<xsl:if test="$left[1]/@type='int' and $right[1]/@type='int'">
										<xsl:attribute name="type" select="'int'"/>
									</xsl:if>
									<xsl:copy-of select="$left"/>
									<xsl:copy-of select="$right"/>
								</op>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:when>
					<xsl:when test="$sub &lt; $add and ends-with(normalize-space($subl),'+')">
						<op kind="sub" type="int" prio="3">
							<xsl:copy-of select="f:toTreeEssence($addl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($subr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$sub &lt; $add and ends-with(normalize-space($subl),'-')">
						<op kind="add" type="int" prio="3">
							<xsl:copy-of select="f:toTreeEssence(replace($subl,'-\s*$',''),$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($subr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$sub &lt; $add and matches($subl,'(\*|\||%)\s*$')">
						<xsl:copy-of select="f:toTreeEssence(concat($subl,'§',$subr),$consts)"/>
					</xsl:when>
					<xsl:when test="$sub &lt; $add">
						<op kind="sub" type="int" prio="3">
							<xsl:copy-of select="f:toTreeEssence($subl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($subr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:otherwise>
						<xsl:message terminate="yes">ERROR: Parsing error in &quot;<xsl:value-of select="$input"/>&quot; !</xsl:message>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- mul/div: * / -->
			<xsl:when test="contains($input,'*') or contains($input,'/')">
				<xsl:variable name="mulr" select="replace($input,'^.*\*','')"/>
				<xsl:variable name="divr" select="replace($input,'^.*/','')"/>
				<xsl:variable name="mul" select="string-length($mulr)"/><!-- after last * -->
				<xsl:variable name="div" select="string-length($divr)"/><!-- after last / -->
				<xsl:choose>
					<xsl:when test="$mul &lt; $div">
						<xsl:variable name="mull" select="substring($input,1,string-length($input)-$mul - 1)"/><!-- before last * -->
						<op kind="mul" type="int" prio="4">
							<xsl:copy-of select="f:toTreeEssence($mull,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($mulr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$div &lt; $mul">
						<xsl:variable name="divl" select="substring($input,1,string-length($input)-$div - 1)"/><!-- before last / -->
						<op kind="div" type="int" prio="4">
							<xsl:copy-of select="f:toTreeEssence($divl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($divr,$consts)"/>
						</op>
					</xsl:when> 
					<xsl:otherwise>
						<xsl:message terminate="yes">ERROR: Parsing error in &quot;<xsl:value-of select="$input"/>&quot; !</xsl:message>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- mod: % %% (was ^) -->
			<xsl:when test="contains($input,'%')">
				<xsl:variable name="modr" select="replace($input,'^.*%','')"/>
				<xsl:variable name="expr" select="replace($input,'^.*%%','')"/>
				<xsl:variable name="mod" select="string-length($modr)"/><!-- after last % -->
				<xsl:variable name="exp" select="string-length($expr)"/><!-- after last %% -->
				<xsl:choose>
					<xsl:when test="$mod &lt; $exp">
						<xsl:variable name="modl" select="substring($input,1,string-length($input)-$mod - 1)"/><!-- before last % -->
						<op kind="mod" type="int" prio="5">
							<xsl:copy-of select="f:toTreeEssence($modl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($modr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:when test="$exp &lt;= $mod">
						<xsl:variable name="expl" select="substring($input,1,string-length($input)-$exp - 2)"/><!-- before last %% -->
						<op kind="exp" type="int" prio="5">
							<xsl:copy-of select="f:toTreeEssence($expl,$consts)"/>
							<xsl:copy-of select="f:toTreeEssence($expr,$consts)"/>
						</op>
					</xsl:when>
					<xsl:otherwise>
						<xsl:message terminate="yes">ERROR: Parsing error in &quot;<xsl:value-of select="$input"/>&quot; !</xsl:message>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<!-- monadic operators -->
			<xsl:when test="contains($input,'!')">
				<op kind="not" type="bool" prio="6">
					<xsl:copy-of select="f:toTreeEssence(substring-after($input,'!'),$consts)"/>
				</op>
			</xsl:when>
			<xsl:when test="starts-with(normalize-space($input),'§')">
				<op kind="sub" type="int" prio="3">
					<op kind="const" type="int" prio="8">0</op>
					<xsl:copy-of select="f:toTreeEssence(substring-after($input,'§'),$consts)"/>
				</op>
			</xsl:when>					
			<!-- constants $$ -->
			<xsl:when test="starts-with(normalize-space($input),'$$')">
				<!--xsl:copy-of select="$consts[@pos=xs:integer(substring-after($input,'$$'))]"/-->
				<xsl:copy-of select="$consts[xs:integer(substring-after($input,'$$'))]"/>
			</xsl:when>
			<!-- variables $ -->
			<xsl:when test="starts-with(normalize-space($input),'$')">
				<op kind="var" prio="7">
					<xsl:if test="matches($input,'^\s*\$[a-z]\s*$')">
						<xsl:attribute name="type" select="'int'"/>
					</xsl:if>
					<xsl:value-of select="normalize-space(substring-after($input,'$'))"/>
				</op>
			</xsl:when>
			<!-- numeric litarals -->
			<xsl:when test="starts-with(upper-case(normalize-space($input)),'0B')">
				<op kind="const" type="int" prio="8">
					<xsl:value-of select="f:str2base(substring(normalize-space($input),3),2)"/>
				</op>
			</xsl:when>
			<xsl:when test="starts-with(upper-case(normalize-space($input)),'0X')">
				<op kind="const" type="int" prio="8">
					<xsl:value-of select="f:str2base(substring(normalize-space($input),3),16)"/>
				</op>
			</xsl:when>
			<xsl:when test="starts-with(upper-case(normalize-space($input)),'0O')">
				<op kind="const" type="int" prio="8">
					<xsl:value-of select="f:str2base(substring(normalize-space($input),3),8)"/>
				</op>
			</xsl:when>
			<xsl:when test="matches(normalize-space($input),'^\d+$')">
				<op kind="const" type="int" prio="8">
					<xsl:value-of select="f:str2base(normalize-space($input),10)"/>
				</op>
			</xsl:when>
			<xsl:otherwise>
				<op kind="const" type="string" prio="8">
					<xsl:value-of select="$input"/>
				</op>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>


	<!-- evaluate syntax tree for a numeric target -->
	<xsl:function name="f:numEssence" as="xs:decimal">
		<xsl:param name="in" as="item()*"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:choose>
			<xsl:when test="$in/@kind='and'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) = 0 or f:numEssence($in/*[2],$context) = 0) then 0 else 1"/>
			</xsl:when>
			<xsl:when test="$in/@kind='or'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) = 0 and f:numEssence($in/*[2],$context) = 0) then 0 else 1"/>
			</xsl:when>
			<xsl:when test="$in/@kind='xor'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) = f:numEssence($in/*[2],$context)) then 0 else 1"/>
			</xsl:when>
			<xsl:when test="$in/@kind=('ge','le','lt','gt','eq','ne','nm','ma') and ($in/*[1]/@type='string' or $in/*[2]/@type='string')">
				<xsl:variable name="left" select="f:textEssence($in/*[1],$context)"/>
				<xsl:variable name="right" select="f:textEssence($in/*[2],$context)"/>
				<xsl:choose>
					<xsl:when test="$in/@kind='nm'">
						<xsl:value-of select="if (contains(string($left),string($right))) then 0 else 1"/><!--Altova kludge-->
					</xsl:when>
					<xsl:when test="$in/@kind='ma'">
						<xsl:value-of select="if (contains(string($left),string($right))) then 1 else 0"/><!--Altova kludge-->
					</xsl:when>
					<xsl:when test="$in/@kind='eq'">
						<xsl:value-of select="if (compare($left,$right) = 0 ) then 1 else 0"/>
					</xsl:when>
					<xsl:when test="$in/@kind='ne'">
						<xsl:value-of select="if (compare($left,$right) = 0 ) then 0 else 1"/>
					</xsl:when>
					<xsl:when test="$in/@kind='lt'">
						<xsl:value-of select="if (compare($left,$right) &lt; 0 ) then 1 else 0"/>
					</xsl:when>
					<xsl:when test="$in/@kind='ge'">
						<xsl:value-of select="if (compare($left,$right) &lt; 0) then 0 else 1"/>
					</xsl:when>
					<xsl:when test="$in/@kind='gt'">
						<xsl:value-of select="if (compare($left,$right) &gt; 0) then 1 else 0"/>
					</xsl:when>
					<xsl:when test="$in/@kind='le'">
						<xsl:value-of select="if (compare($left,$right) &gt; 0) then 0 else 1"/>
					</xsl:when>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='ge'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) &lt; f:numEssence($in/*[2],$context)) then 0 else 1"/>
			</xsl:when>
			<xsl:when test="$in/@kind='le'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) &gt; f:numEssence($in/*[2],$context)) then 0 else 1"/>
			</xsl:when>
			<xsl:when test="$in/@kind='gt'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) &gt; f:numEssence($in/*[2],$context)) then 1 else 0"/>
			</xsl:when>
			<xsl:when test="$in/@kind='lt'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) &lt; f:numEssence($in/*[2],$context)) then 1 else 0"/>
			</xsl:when>
			<xsl:when test="$in/@kind='eq'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) = f:numEssence($in/*[2],$context)) then 1 else 0"/>
			</xsl:when>
			<xsl:when test="$in/@kind='ne'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) = f:numEssence($in/*[2],$context)) then 0 else 1"/>
			</xsl:when>
			<xsl:when test="$in/@kind='add'">
				<xsl:value-of select="f:numEssence($in/*[1],$context) + f:numEssence($in/*[2],$context)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='sub'">
				<xsl:value-of select="f:numEssence($in/*[1],$context) - f:numEssence($in/*[2],$context)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mul'">
				<xsl:value-of select="f:numEssence($in/*[1],$context) * f:numEssence($in/*[2],$context)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='div'">
				<xsl:variable name="divisor" select="f:numEssence($in/*[2],$context)"/>
				<xsl:if test="$divisor = 0">
					<xsl:message terminate="yes">ERROR: Divide by 0!</xsl:message>
				</xsl:if>
				<!-- xsl:value-of select="floor(f:numEssence($in/*[1],$context) div $divisor)"/ -->
				<!-- xsl:value-of select="xs:integer(f:numEssence($in/*[1],$context) div $divisor)"/ -->
				<xsl:value-of select="f:numEssence($in/*[1],$context) idiv $divisor"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mod'">
				<xsl:variable name="class" select="f:numEssence($in/*[2],$context)"/>
				<xsl:if test="$class = 0">
					<xsl:message terminate="yes">ERROR: modulo  0!</xsl:message>
				</xsl:if>
				<xsl:value-of select="f:numEssence($in/*[1],$context) mod $class"/>
			</xsl:when>
			<xsl:when test="$in/@kind='exp'">
				<xsl:variable name="b" select="f:numEssence($in/*[1],$context)"/>
				<xsl:variable name="e" select="f:numEssence($in/*[2],$context)"/>
				<xsl:choose>
					<xsl:when test="$b = 1">
						<xsl:value-of select="1"/>
					</xsl:when>
					<xsl:when test="$b = 0">
						<xsl:value-of select="0"/>
					</xsl:when>
					<xsl:when test="$e &lt; 1">
						<xsl:value-of select="1"/>
					</xsl:when>
					<xsl:when test="$e = 1">
						<xsl:value-of select="$b"/>
					</xsl:when>
					<xsl:when test="false() and $b mod 2 = 0 and $e &gt; 63"><!-- preserve property 'even' -->
						<xsl:value-of select="xs:integer(f:power(2,64))"/>
					</xsl:when>
					<xsl:when test="false() and $b != 2 and $b mod 2 = 0"><!-- preserve property 'even' -->						
						<xsl:variable name="h" select="f:power($b div 2, xs:integer($e))"/>
						<xsl:value-of select="xs:integer(($h mod f:power(2,64-$e))*f:power(2,$e))"/>
					</xsl:when>
					<xsl:when test="$b = 2">
						<xsl:value-of select="xs:decimal(f:power2(xs:integer($e)))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="xs:decimal(f:power($b, xs:integer($e)))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='not'">
				<xsl:value-of select="if (f:numEssence($in/*[1],$context) = 0) then 1 else 0"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const' and $in/@type=('int','bool')">
				<xsl:choose>
					<xsl:when test="starts-with(upper-case($in/text()),'0B')">
						<xsl:value-of select="f:str2base(substring($in/text(),3),2)"/>
					</xsl:when>
					<xsl:when test="starts-with(upper-case($in/text()),'0X')">
						<xsl:value-of select="f:str2base(substring($in/text(),3),16)"/>
					</xsl:when>
					<xsl:when test="starts-with(upper-case($in/text()),'0O')">
						<xsl:value-of select="f:str2base(substring($in/text(),3),8)"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="$in/text()"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='const' and $in/@type='string' and matches($in/text(),'^\d+$')">
				<xsl:value-of select="xs:decimal($in/text())"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const'">
				<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}" select="concat('ERROR: Non-numeric value ',$in)"/>
				<xsl:message terminate="no">Replaced by -1</xsl:message>
				<xsl:value-of select="-1"/>
			</xsl:when>
			<xsl:when test="$in/@kind='var'">
				<xsl:variable name="getparameter" as="xs:string*">
					<xsl:for-each select="$ParaMaps2/key('parameter',concat($context,':',$in/text()))/*[ends-with(local-name(),'Value')]">
						<xsl:sort data-type="number" select="string-length(local-name())"/>
						<xsl:value-of select="text()"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="count($getparameter) &gt; 0 and string-length($getparameter[1])">
						<xsl:value-of select="f:numEssence(f:parseEssence($getparameter[1]),$context)"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: Unresolved parameter "<xsl:value-of 
									select="$in/text()"/>"!</xsl:message>
						<xsl:message terminate="no">Replaced by -1</xsl:message>
						<xsl:value-of select="-1"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and count($in/*)!=3">
				<xsl:message terminate="yes">ERROR: Wrong number of parameters for function <xsl:value-of select="$in/*[1]/text()"/></xsl:message>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='min'">
				<xsl:variable name="paras" as="xs:integer*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:numEssence(.,$context)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="if ($paras[1]&lt;$paras[2]) then $paras[1] else $paras[2]"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='max'">
				<xsl:variable name="paras" as="xs:integer*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:numEssence(.,$context)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="if ($paras[1]&gt;$paras[2]) then $paras[1] else $paras[2]"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='rshift'">
				<xsl:variable name="paras" as="xs:integer*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:numEssence(.,$context)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="$paras[2]=0">
						<xsl:value-of select="$paras[1]"/>
					</xsl:when>
					<xsl:when test="$paras[2]&lt;0">
						<xsl:value-of select="$paras[1] * xs:decimal(f:power(2, xs:integer(-$paras[2])))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="$paras[1] idiv xs:decimal(f:power(2, xs:integer($paras[2])))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='lshift'">
				<xsl:variable name="paras" as="xs:integer*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:numEssence(.,$context)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="$paras[2]=0">
						<xsl:value-of select="$paras[1]"/>
					</xsl:when>
					<xsl:when test="$paras[2]&lt;0">
						<xsl:value-of select="$paras[1] idiv xs:decimal(f:power(2, xs:integer(-$paras[2])))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="$paras[1] * xs:decimal(f:power(2, xs:integer($paras[2])))"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='log'">
				<xsl:variable name="paras" as="xs:integer*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:numEssence(.,$context)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="f:log($paras[1],$paras[2])"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='pos'">
				<xsl:variable name="index" as="xs:decimal" select="f:numEssence($in/*[3],$context)"/>
				<xsl:variable name="paras" as="item()*">
					<xsl:choose>
						<xsl:when test="$in/*[2]/@kind='func' and $in/*[2]/*[1]/text()='list'">
							<xsl:for-each select="$in/*[2]/*">
								<xsl:if test="position()-2 = $index">
									<xsl:copy-of select="."/>
								</xsl:if>
							</xsl:for-each>
						</xsl:when>
						<xsl:when test="$in/*[2]/@kind='var'">
							<xsl:variable name="getparameter" as="xs:string*">
								<xsl:for-each select="$ParaMaps2/key('parameter',concat($context,':',$in/*[2]/text()))/*[ends-with(local-name(),'Value')]">
									<xsl:sort data-type="number" select="string-length(local-name())"/>
									<xsl:value-of select="text()"/>
								</xsl:for-each>
							</xsl:variable>
							<xsl:choose>
								<xsl:when test="count($getparameter) &gt; 0 and string-length($getparameter[1])">
									<xsl:variable name="tree" as="item()" select="f:parseEssence($getparameter[1])"/>!--TODO pruning and index interpolation -->
									<xsl:choose>
										<xsl:when test="$tree/@kind='func' and $tree/*[1]/text()='list'">
											<xsl:for-each select="$tree/*">
												<xsl:if test="position()-2 = $index">
													<xsl:copy-of select="."/>
												</xsl:if>
											</xsl:for-each>
										</xsl:when>
										<xsl:otherwise>
											<xsl:message terminate="yes">ERROR: Invalid first parameter in "pos(<xsl:value-of 
														select="$in/*[2]/text()"/>,...)"!</xsl:message>
										</xsl:otherwise>
									</xsl:choose>
								</xsl:when>
								<xsl:otherwise>
									<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: Unresolved parameter "<xsl:value-of 
											select="$in/text()"/>"!</xsl:message>
									<xsl:message terminate="no">Replaced by -1</xsl:message>
									<xsl:value-of select="-1"/>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:when>
						<xsl:otherwise>
							<xsl:message terminate="yes">ERROR: Invalid first parameter in "pos()"!</xsl:message>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="count($paras)">
						<xsl:sequence select="f:numEssence($paras[1],$context)"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: pos(<xsl:value-of 
									select="$in/*[2]"/>,<xsl:value-of select="$index"/>) index out of bounds!</xsl:message>
						<xsl:message terminate="no">pos(...) replaced by -1</xsl:message>
						<xsl:value-of select="-1"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:otherwise>
				<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: Non-numeric value !</xsl:message>
				<xsl:message terminate="no">Replaced by -1</xsl:message>
				<xsl:value-of select="-1"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- evaluate syntax tree for a textual target -->
	<xsl:function name="f:textEssence" as="xs:string">
		<xsl:param name="in" as="item()*"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:choose>
			<xsl:when test="not($in/@kind)"><xsl:value-of select="''"/></xsl:when>
			<xsl:when test="$in/@kind=('cat')">
				<xsl:value-of select="concat(f:textEssence($in/*[1],$context),f:textEssence($in/*[2],$context))"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const' and $in/text()='#'">
				<xsl:value-of select="$in/text()"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const'">
				<xsl:value-of select="replace($in/text(),'&amp;amp;','&amp;')"/><!--TODO: check this for lt and gt -->
			</xsl:when>
			<xsl:when test="$in/@kind='var' and $in/text()='suppress' and string-length($suppress)">
				<xsl:value-of select="$suppress"/>
			</xsl:when>
			<xsl:when test="$in/@kind='var'">
				<xsl:variable name="getparameter" as="xs:string*">
					<xsl:for-each select="$ParaMaps2/key('parameter',concat($context,':',$in/text()))/*[ends-with(local-name(),'Value')]">
						<xsl:sort data-type="number" select="string-length(local-name())"/>
						<xsl:value-of select="replace(text(),'^&quot;(.*)&quot;$','$1')"/>
					</xsl:for-each>
					<xsl:if test="$ParaMaps2/filter[@Int_Class_ID=$context]">
						<xsl:copy-of select="f:getfilter($in/text(),$context)"/>
					</xsl:if>
					<!-- xsl:value-of select="concat('$',$in/text())"/ -->
					<xsl:value-of select="$in/text()"/>
				</xsl:variable>
				<xsl:if test="count($getparameter) &lt; 2">
					<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}" 
							select="concat('ERROR: Unresolved parameter &quot;',$in/text(),'&quot;!')"/>
					<xsl:message terminate="no">Replaced by "<xsl:value-of select="$getparameter[1]"/>"</xsl:message>
				</xsl:if>
				<xsl:value-of select="$getparameter[1]"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='pos' and count($in/*)=3">
				<xsl:variable name="index" as="xs:decimal" select="f:numEssence($in/*[3],$context)"/>
				<xsl:variable name="paras" as="item()*">
					<xsl:choose>
						<xsl:when test="$in/*[2]/@kind='func' and $in/*[2]/*[1]/text()='list'">
							<xsl:for-each select="$in/*[2]/*">
								<xsl:if test="position()-2 = $index">
									<xsl:copy-of select="."/>
								</xsl:if>
							</xsl:for-each>
						</xsl:when>
						<xsl:when test="$in/*[2]/@kind='var'">
							<xsl:variable name="getparameter" as="xs:string*">
								<xsl:for-each select="$ParaMaps2/key('parameter',concat($context,':',$in/*[2]/text()))/*[ends-with(local-name(),'Value')]">
									<xsl:sort data-type="number" select="string-length(local-name())"/>
									<xsl:value-of select="text()"/>
								</xsl:for-each>
							</xsl:variable>
							<xsl:choose>
								<xsl:when test="count($getparameter) &gt; 0 and string-length($getparameter[1])">
									<xsl:variable name="tree" as="item()" select="f:parseEssence($getparameter[1])"/><!--TODO pruning and index interpolation -->
									<xsl:choose>
										<xsl:when test="$tree/@kind='func' and $tree/*[1]/text()='list'">
											<xsl:for-each select="$tree/*">
												<xsl:if test="position()-2 = $index">
													<xsl:copy-of select="."/>
												</xsl:if>
											</xsl:for-each>
										</xsl:when>
										<xsl:otherwise>
											<xsl:message terminate="yes">ERROR: Invalid first parameter in "pos(<xsl:value-of 
														select="$in/*[2]/text()"/>,...)"!</xsl:message>
										</xsl:otherwise>
									</xsl:choose>
								</xsl:when>
								<xsl:otherwise>
									<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: Unresolved parameter "<xsl:value-of 
											select="$in/text()"/></xsl:message>
									<xsl:message terminate="no">Replaced by -1</xsl:message>
									<xsl:value-of select="-1"/>
								</xsl:otherwise>
							</xsl:choose>
						</xsl:when>
						<xsl:otherwise>
							<xsl:message terminate="yes">ERROR: Invalid first parameter in "pos()"!</xsl:message>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="count($paras)">
						<xsl:sequence select="f:textEssence($paras[1],$context)"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: pos(<xsl:value-of 
									select="$in/*[2]"/>,<xsl:value-of select="$index"/>) index out of bounds!</xsl:message>
						<xsl:message terminate="no">Replaced by -1</xsl:message>
						<xsl:value-of select="-1"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='dec' and count($in/*)=3">
				<xsl:variable name="paras" as="xs:decimal*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:numEssence(.,$context)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:variable name="s" select="string($paras[2])" as="xs:string"/>
				<xsl:variable name="p" select="for $i in string-length($s) +1 to xs:integer($paras[1]) return '0'" as="xs:string*"/>
				<xsl:value-of select="concat(string-join($p,''),$s)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='hex' and count($in/*)=3">
				<xsl:variable name="paras" as="xs:decimal*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:numEssence(.,$context)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:variable name="s" select="f:decimal-to-hex($paras[2])" as="xs:string"/>
				<xsl:variable name="p" select="for $i in string-length($s) +1 to xs:integer($paras[1]) return '0'" as="xs:string*"/>
				<xsl:value-of select="concat(string-join($p,''),$s)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='bin' and count($in/*)=3">
				<xsl:variable name="paras" as="xs:decimal*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:numEssence(.,$context)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:variable name="s" select="f:decimal-to-bin($paras[2])" as="xs:string"/>
				<xsl:variable name="p" select="for $i in string-length($s) +1 to xs:integer($paras[1]) return '0'" as="xs:string*"/>
				<xsl:value-of select="concat(string-join($p,''),$s)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func' and $in/*[1]/text()='eng' and count($in/*)=2">
				<xsl:variable name="val" as="xs:decimal" select="f:numEssence($in/*[2],$context)"/>
				<xsl:variable name="p" as="xs:string*">
					<xsl:choose>
						<xsl:when test="$val &gt;= 1073741824">
							<xsl:value-of select="floor($val div 10737418.24) div 100"/>
							<xsl:text>GB</xsl:text>
						</xsl:when>
						<xsl:when test="$val &gt;= 1048576">
							<xsl:value-of select="floor($val div 10485.76) div 100"/>
							<xsl:text>MB</xsl:text>
						</xsl:when>
						<xsl:when test="$val &gt;= 1024">
							<xsl:value-of select="floor($val div 10.24) div 100"/>
							<xsl:text>KB</xsl:text>
						</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="$val"/>
							<xsl:text>B</xsl:text>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>						
				<xsl:value-of select="string-join($p,'')"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:value-of select="f:numEssence($in,$context)"/>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- translate the syntax tree back to Essence -->
	<xsl:function name="f:stringifyEssence" as="xs:string">
		<xsl:param name="in" as="item()*"/>
		<xsl:value-of select="f:stringifyEssence($in,0)"/>
	</xsl:function>
	<xsl:function name="f:stringifyEssence" as="xs:string">
		<xsl:param name="in" as="item()*"/>
		<xsl:param name="prio" as="xs:integer"/>
		<xsl:variable name="pre" select="if ($in/@prio &lt;= $prio) then '(' else ''"/>
		<xsl:variable name="post" select="if ($in/@prio &lt;= $prio) then ')' else ''"/>
		<xsl:choose>
			<xsl:when test="$in/@kind='and'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' &amp; ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='or'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' | ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='xor'"><!-- enforce brackets -->
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],9),' ^ ',f:stringifyEssence($in/*[2],9),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='ge'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' &gt;= ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='le'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' &lt;= ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='gt'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' &gt; ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='lt'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' &lt; ', f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='eq'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' == ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='ne'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' != ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='nm'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' !~ ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='ma'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' =~ ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='add'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' + ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='cat'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' + ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='sub'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' - ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mul'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' * ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='div'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' / ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mod'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' % ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='exp'">
				<xsl:value-of select="concat($pre,f:stringifyEssence($in/*[1],$in/@prio),' ^ ',f:stringifyEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='not'">
				<xsl:value-of select="concat('!',$pre,f:stringifyEssence($in/*[1],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const' and $in/@type='string' and contains($in/text(),'&quot;')">
				<xsl:value-of select='concat("&apos;",$in/text(),"&apos;")'/>
			</xsl:when>
			<xsl:when test="$in/@kind='const' and $in/@type='string' and $in/text()='#'">
				<xsl:value-of select="$in/text()"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const' and $in/@type='string'">
				<xsl:value-of select="concat('&quot;',$in/text(),'&quot;')"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const' and $in/@type='bool'">
				<xsl:value-of select="if ($in/text()=0) then 'false' else 'true'"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const'">
				<xsl:value-of select="$in/text()"/>
			</xsl:when>
			<xsl:when test="$in/@kind='var'">
				<xsl:value-of select="concat('$',$in/text())"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func'">
				<xsl:variable name="paras" as="xs:string*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:value-of select="f:stringifyEssence(.,0)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="string-join(($pre,$in/*[1]/text(),'(',string-join($paras,','),')',$post),'')"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:message terminate="yes">ERROR: Undefined expression operator "<xsl:value-of select="$in/@kind"/>"!</xsl:message>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- minimize the syntax tree (constant folding, mapping of parameters if context is given, mapping of local variables if mapping is given -->
	<!-- map all parameters and variables, but keep the filter attributes. Annotate filter attributes with the number of negations -->
	<xsl:function name="f:pruneEssence" as="item()*">
		<xsl:param name="in" as="item()*"/>
		<xsl:copy-of select="f:pruneEssence($in,'0',(),0)"/>
	</xsl:function>
	<xsl:function name="f:pruneEssence" as="item()*">
		<xsl:param name="in" as="item()*"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:copy-of select="f:pruneEssence($in,$context,(),0)"/>
	</xsl:function>
	<xsl:function name="f:pruneEssence" as="item()*">
		<xsl:param name="in" as="item()*"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:param name="varmap" as="item()*"/>
		<xsl:param name="pol" as="xs:integer"/>
		<!-- 0 means not used, 1 means "used in =~", -1 means "used in !~" -->
		<xsl:variable name="left" as="item()*">
			<xsl:if test="count($in/*) &gt; 0">
				<xsl:copy-of select="f:pruneEssence($in/*[1],$context,$varmap,$pol)"/>
			</xsl:if>
		</xsl:variable>
		<xsl:variable name="right" as="item()*">
			<xsl:if test="count($in/*) &gt; 1">
				<xsl:copy-of select="f:pruneEssence($in/*[2],$context,$varmap,$pol)"/>
			</xsl:if>
		</xsl:variable>
		<xsl:choose>
			<xsl:when test="$in/@kind='func'">
				<xsl:variable name="lastp" select="f:pruneEssence($in/*[last()],$context,$varmap,$pol)"/>
				<xsl:choose>
					<xsl:when test="count($in/*)!=3">
						<op>
							<xsl:copy-of select="$in/@*|$in/*[1]"/>
							<xsl:copy-of select="$right"/>
							<xsl:for-each select="$in/*[position()&gt;2]">
								<xsl:copy-of select="f:pruneEssence(.,$context,$varmap,$pol)"/>
							</xsl:for-each>
						</op>
					</xsl:when>
					<xsl:when test="$in/*[1]/text()=('lshift','rshift') and $right/@kind='const' and $right/text()='0'">
						<xsl:copy-of select="$right"/>
					</xsl:when>
					<xsl:when test="$in/*[1]/text()=('lshift','rshift') and $lastp/@kind='const' and $lastp/text()='0'">
						<xsl:copy-of select="$right"/>
					</xsl:when>
					<xsl:when test="$in/*[1]/text()=('min','max','lshift','rshift','log') and $right/@kind='const' and $lastp/@kind='const'">
						<xsl:variable name="res" as="item()">
							<op>
								<xsl:copy-of select="$in/@*|$in/*[1]"/>
								<xsl:copy-of select="$right"/>
								<xsl:copy-of select="$lastp"/>
							</op>
						</xsl:variable>
						<op kind="const" type="int" prio="8">
							<xsl:value-of select="f:numEssence($res,'0')"/>
						</op>
					</xsl:when>
					<xsl:when test="$in/*[1]/text()='pos' and $lastp/@kind='const'">
						<xsl:variable name="index" as="xs:decimal" select="f:numEssence($lastp,$context)"/>
						<xsl:variable name="paras" as="item()*">
							<xsl:choose>
								<xsl:when test="$right/@kind='func' and $right/*[1]/text()='list'">
									<xsl:for-each select="$right/*">
										<xsl:if test="position()-2 = $index">
											<xsl:copy-of select="."/>
										</xsl:if>
									</xsl:for-each>
								</xsl:when>
								<xsl:when test="$right/@kind='var' and $ParaMaps2/key('parameter',concat($context,':',$right/text()))">
									<xsl:for-each select="$ParaMaps2/key('parameter',concat($context,':',$right/text()))/*[ends-with(local-name(),'Value')]">
										<xsl:sort data-type="number" select="string-length(local-name())"/>
										<xsl:if test="position()=1">
											<xsl:choose>
												<xsl:when test="../DataType/@xsi:type='Array'">
													<xsl:variable name="tree" as="item()" select="f:parseEssence(replace(.,'^&quot;(list.*)&quot;$','$1'))"/>
													<xsl:choose>
														<xsl:when test="$tree/@kind='func' and $tree/*[1]/text()='list'">
															<xsl:for-each select="$tree/*">
																<xsl:if test="position()-2 = $index">
																	<xsl:copy-of select="."/>
																</xsl:if>
															</xsl:for-each>
														</xsl:when>
														<xsl:otherwise>
															<xsl:message terminate="yes">ERROR: Invalid value in parameter "pos(<xsl:value-of 
																		select="$right/text()"/>,...)"!</xsl:message>
														</xsl:otherwise>
													</xsl:choose>
												</xsl:when>
											</xsl:choose>
										</xsl:if>
									</xsl:for-each>
								</xsl:when>
							</xsl:choose>
						</xsl:variable>
						<xsl:choose>
							<xsl:when test="count($paras)">
								<xsl:sequence select="f:pruneEssence($paras[1],$context,$varmap,$pol)"/>
							</xsl:when>
							<xsl:otherwise>
								<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: pos(<xsl:value-of 
											select="$right"/>,<xsl:value-of select="$index"/>) index out of bounds!</xsl:message>
								<xsl:message terminate="no">pos(...) replaced by -1</xsl:message>
								<xsl:value-of select="-1"/>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:when>
					<xsl:otherwise>
						<op>
							<xsl:copy-of select="$in/@*|$in/*[1]"/>
							<xsl:copy-of select="$right"/>
							<xsl:copy-of select="$lastp"/>
						</op>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='not' and $pol != 0">
				<xsl:choose>
					<xsl:when test="$left/@kind='not'">
						<xsl:copy-of select="f:pruneEssence($left/*[1],$context,$varmap,$pol)"/>
					</xsl:when>
					<xsl:when test="$left/@kind='const'">
						<op>
							<xsl:copy-of select="$left/@*"/>
							<xsl:value-of select="if ($left/text()='0') then 1 else 0"/>
						</op>
					</xsl:when>
					<xsl:otherwise>
						<op>
							<xsl:copy-of select="$in/@*|f:pruneEssence($in/*[1],$context,$varmap,-$pol)"/>
						</op>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='not'">
				<xsl:choose>
					<xsl:when test="$left/@kind='not'">
						<xsl:copy-of select="$left/*[1]"/>
					</xsl:when>
					<xsl:when test="$left/@kind='const'">
						<op>
							<xsl:copy-of select="$left/@*"/>
							<xsl:value-of select="if ($left/text()='0') then 1 else 0"/>
						</op>
					</xsl:when>
					<xsl:otherwise>
						<op>
							<xsl:copy-of select="$in/@*|$left"/>
						</op>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='var' and $in/text()='suppress' and string-length($suppress)">
				<op kind="const" prio="8">
					<xsl:attribute name="type" select="'string'"/>
					<xsl:value-of select="$suppress"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='var' and $ParaMaps2/key('parameter',concat($context,':',$in/text()))">
				<xsl:for-each select="$ParaMaps2/key('parameter',concat($context,':',$in/text()))/*[ends-with(local-name(),'Value')]">
					<xsl:sort data-type="number" select="string-length(local-name())"/>
					<xsl:if test="position()=1">
						<xsl:choose>
							<xsl:when test="../DataType/@xsi:type='Array'">
								<xsl:copy-of select="$in"/>
							</xsl:when>
							<xsl:when test="contains(lower-case(../@xsi:type),'integer')">
								<xsl:variable name="numpar" select="f:numEssence(f:parseEssence(text()),$context)"/>
								<xsl:choose>
									<xsl:when test="number($numpar)&gt;=281474976710656">
										<op kind="const" prio="8" type="int">
											<xsl:copy-of select="text()"/>
										</op>
									</xsl:when>
									<xsl:otherwise>
										<op kind="const" prio="8" type="int">
											<xsl:value-of select="$numpar"/>
										</op>
									</xsl:otherwise>
								</xsl:choose>
							</xsl:when>
							<xsl:when test="contains(lower-case(../@xsi:type),'boolean')">
								<xsl:variable name="numpar" select="f:numEssence(f:parseEssence(text()),$context)"/>
								<op kind="const" prio="8" type="bool">
									<xsl:value-of select="$numpar"/>
								</op>
							</xsl:when>							
							<xsl:when test="not(text())"/>
							<xsl:otherwise>
								<op kind="const" prio="8" type="string">
									<xsl:value-of select="f:textEssence(f:parseEssence(text()),$context)"/>
								</op>
							</xsl:otherwise>
						</xsl:choose>
					</xsl:if>
				</xsl:for-each>
			</xsl:when>
			<xsl:when test="$in/@kind='var' and $pol=0 and $ParaMaps2/filter[@Int_Class_ID=$context]/*[@Name=$in/text()]">
				<op kind="const" prio="8">
					<xsl:for-each select="$ParaMaps2/key('filter',concat($context,':',$in/text()))/*[ends-with(local-name(),'Value')]">
						<xsl:sort data-type="number" select="string-length(local-name())"/>
						<xsl:if test="position()=1">
							<xsl:attribute name="type" select="'string'"/>
							<xsl:value-of select="f:textEssence(f:parseEssence(text()),$context)"/>
						</xsl:if>
					</xsl:for-each>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='var' and count($varmap) &gt; 0 and $varmap[@Name=$in/text()]">
				<op kind="const" prio="8">
					<xsl:attribute name="type"><xsl:choose><xsl:when test="matches(($varmap[@Name=$in/text()])[1]/text(),'^\d')">int</xsl:when><xsl:otherwise>string</xsl:otherwise></xsl:choose></xsl:attribute>
					<xsl:value-of select="($varmap[@Name=$in/text()])[1]/text()"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='var' and $ParaMaps2/filter[@Int_Class_ID=$context]/*[@Name=$in/text()]">
				<op>
					<xsl:attribute name="pol" select="$pol"/>
					<xsl:copy-of select="$in/@*[local-name()!='pol']|$in/text()"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='const' or $in/@kind='var'">
				<xsl:copy-of select="$in"/>
			</xsl:when>
			<xsl:when test="$in/@kind='and' and $left/@kind='const' and $left/text()='0'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='and' and $right/@kind='const' and $right/text()='0'">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='and' and $left/@kind='const'">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='and' and $right/@kind='const'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='or' and $left/@kind='const' and $left/text()='1'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='or' and $right/@kind='const' and $right/text()='1'">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='or' and $left/@kind='const'">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='or' and $right/@kind='const'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='xor' and $left/@kind='const' and $right/@kind='const'">
				<op kind="const" type="bool" prio="8">
					<xsl:value-of select="if ($right/text() = $left/text()) then 0 else 1"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='xor' and $left/@kind='const' and $left/text()='1'">
				<op kind="not" type="bool" prio="6">
					<xsl:copy-of select="$right"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='xor' and $right/@kind='const' and $right/text()='1'">
				<xsl:copy-of select="$right"/>
				<op kind="not" type="bool" prio="6">
					<xsl:copy-of select="$left"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='xor' and $left/@kind='const'">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='xor' and $right/@kind='const'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='add' and $left/@kind='const' and $left/text()='0' and $right/@type='int'">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='add' and $right/@kind='const' and $right/text()='0' and $left/@type='int'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='add' and $left/@kind='const' and $left/@type='int' and $right/@kind='const' and $right/@type='int'">
				<op>
					<xsl:copy-of select="$left/@*"/>
					<xsl:value-of select="xs:decimal($left/text()) + xs:decimal($right/text())"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='cat' and $left/@kind='const' and string-length($left/text())=0">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='cat' and $right/@kind='const' and string-length($right/text())=0">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='cat' and $left/@kind='const' and $right/@kind='const'">
				<op>
					<xsl:copy-of select="$left/@*"/>
					<xsl:attribute name="type" select="'string'"/>
					<xsl:if test="$in/*[1]/@kind='var' 
									and count($varmap) != 0 
									and $varmap[@Name=$in/*[1]/text() and @fmt]">
						<xsl:value-of select="substring($varmap[@Name=$in/*[1]/text()]/@fmt,1+string-length($left/text()))"/>
					</xsl:if>
					<xsl:value-of select="$left/text()"/>
					<xsl:if test="$in/*[2]/@kind='var' 
									and count($varmap) != 0 
									and $varmap[@Name=$in/*[2]/text() and @fmt]">
						<xsl:value-of select="substring($varmap[@Name=$in/*[2]/text()]/@fmt,1+string-length($right/text()))"/>
					</xsl:if>
					<xsl:value-of select="$right/text()"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='sub' and $right/@kind='const' and $right/text()='0'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='sub' and $left/@kind='const' and $left/@type='int' 
											and $right/@kind='const' and $right/@type='int'">
				<op>
					<xsl:copy-of select="$left/@*"/>
					<xsl:value-of select="xs:decimal($left/text()) - xs:decimal($right/text())"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='mul' and $left/@kind='const' and $left/text()='0'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mul' and $right/@kind='const' and $right/text()='0'">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mul' and $left/@kind='const' and $left/text()='1'">
				<xsl:copy-of select="$right"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mul' and $right/@kind='const' and $right/text()='1'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='div' and $right/@kind='const' and $right/text()='1'">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mod' and $right/@kind='const' and number($right/text()) &lt; 2">
				<op kind="const" type="int" prio="8">0</op>
			</xsl:when>
			<xsl:when test="$in/@kind='exp' and $right/@kind='const' and number($right/text()) &lt; 1">
				<op kind="const" type="int" prio="8">1</op>
			</xsl:when>
			<xsl:when test="$in/@kind='exp' and $right/@kind='const' and number($right/text()) &lt; 2">
				<xsl:copy-of select="$left"/>
			</xsl:when>
			<xsl:when test="$in/@kind='nm' and $left/@pol != 0">
				<op>
					<xsl:attribute name="pol" select="$pol"/>
					<xsl:copy-of select="$in/@*"/>
					<op>
						<xsl:attribute name="pol" select="-($left/@pol)"/>
						<xsl:copy-of select="$left/@*[local-name()!='pol']|$left/text()"/>
					</op>
					<xsl:copy-of select="$right"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind='ma' and $left/@pol != 0">
				<op>
					<xsl:attribute name="pol" select="$pol"/>
					<!-- xsl:copy-of select="$in/@*|$left|$right"/-->
					<xsl:copy-of select="$in/@*"/>
					<xsl:copy-of select="$left"/>
					<xsl:copy-of select="$right"/>
				</op>
			</xsl:when>
			<xsl:when test="$in/@kind=('ma','eq') and not($left/@kind) and not($right/@kind)">
				<op kind="const" type="bool" prio="8">1</op>			
			</xsl:when>
			<xsl:when test="$in/@kind=('nm','ne') and not($left/@kind) and not($right/@kind)">
				<op kind="const" type="bool" prio="8">0</op>			
			</xsl:when>
			<xsl:when test="$in/@kind=('ma','eq') and not($left/@kind)">
				<op kind="const" type="bool" prio="8">0</op>			
			</xsl:when>
			<xsl:when test="$in/@kind=('nm','ne') and not($left/@kind)">
				<op kind="const" type="bool" prio="8">1</op>			
			</xsl:when>
			<xsl:when test="$in/@kind=('ma','ne') and not($right/@kind)">
				<op kind="const" type="bool" prio="8">1</op>			
			</xsl:when>
			<xsl:when test="$in/@kind=('nm','eq') and not($right/@kind)">
				<op kind="const" type="bool" prio="8">0</op>			
			</xsl:when>
			<xsl:otherwise>
				<!-- constant folding of all duadic operators ge,le,gt,lt,eq,ne,nm,ma,add,cat,sub,mul,div,mod,exp  -->
				<xsl:variable name="res" as="item()*">
					<op>
						<xsl:copy-of select="$in/@*"/>
						<xsl:copy-of select="$left"/>
						<xsl:copy-of select="$right"/>
					</op>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="($left/@kind='const' and $left/text()='#') or ($right/@kind='const' and $right/text()='#')">
						<xsl:copy-of select="$res"/>
					</xsl:when>
					<xsl:when test="$left/@kind='const' and $right/@kind='const' and $in/@type='int'">
						<op kind="const" type="int" prio="8">
							<xsl:value-of select="f:numEssence($res,'0')"/>
						</op>
					</xsl:when>
					<xsl:when test="$left/@kind='const' and $right/@kind='const' and $in/@type='bool'">
						<op kind="const" type="bool" prio="8">
							<xsl:value-of select="f:numEssence($res,'0')"/>
						</op>
					</xsl:when>
					<xsl:when test="$left/@kind='const' and $right/@kind='const' and $in/@type='string'">
						<op kind="const" type="string" prio="8">
							<xsl:value-of select="f:textEssence($res,'0')"/>
						</op>
					</xsl:when>
					<xsl:otherwise>
						<xsl:copy-of select="$res"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!--	-->
	<!-- decompose Hidden element into filter attributes and "Rest" -->
	<xsl:function name="f:parseHidden" as="item()*">
		<xsl:param name="in"/>
		<xsl:if test="string-length($in)">
			<xsl:copy-of select="f:parseHidden($in,'0',())"/>
		</xsl:if>
	</xsl:function>
	<xsl:function name="f:parseHidden" as="item()*">
		<xsl:param name="in" as="xs:string"/>
		<xsl:param name="context" as="xs:string"/>
		<xsl:param name="varmap" as="item()*"/>
		<xsl:copy-of select="f:decodeHidden(f:pruneEssence(f:parseEssence($in),$context,$varmap,1))"/>
	</xsl:function>
	<xsl:function name="f:decodeHidden" as="item()*">
		<xsl:param name="tree" as="item()*"/>
		<!-- xsl:for-each-group select="$tree/descendant-or-self::*[local-name()='op' and @kind='var' and @pol=1]" group-by="text()">
			<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: Illegal use of attribute <xsl:value-of 
						select="current-grouping-key()"/>! Can't use XPath filtering this way. Negated value (no_*) inferred.</xsl:message>
			<problem kind="negated match">
				<xsl:value-of select="current-grouping-key()"/>
			</problem>
			</xsl:for-each>
		</xsl:for-each-group -->
		<xsl:for-each-group select="$tree/descendant-or-self::*[local-name()='op' and @kind='var' and not( ../@kind='ma' or ../@kind='nm') and @pol]" group-by="text()">
			<xsl:message terminate="{if ($warning='fatal') then 'yes' else 'no'}">ERROR: Illegal use of attribute <xsl:value-of 
						select="current-grouping-key()"/>! Only !~ and =~ operators supported.</xsl:message>
			<problem kind="not a match operator">
				<xsl:value-of select="current-grouping-key()"/>
			</problem>
		</xsl:for-each-group>
		<xsl:for-each-group select="$tree/descendant-or-self::*[local-name()='op' and (@kind='ma' or @kind='nm') and ./*[1]/@pol=-1]" group-by="./*[1]/text()">
			<xsl:for-each select="current-group()">
				<xsl:element name="{current-grouping-key()}">
					<xsl:value-of select="f:textEssence(./*[2],'0')"/>
				</xsl:element>
			</xsl:for-each>
		</xsl:for-each-group>
		<xsl:for-each-group select="$tree/descendant-or-self::*[local-name()='op' and (@kind='ma' or @kind='nm') and ./*[1]/@pol=1]" group-by="./*[1]/text()">
			<xsl:for-each select="current-group()">
				<xsl:variable name="val" select="f:textEssence(./*[2],'0')"/>
				<xsl:choose>
					<xsl:when test="starts-with($val,'no_')">
						<xsl:element name="{current-grouping-key()}">
							<xsl:value-of select="replace($val,'^no_','has_')"/>
						</xsl:element>
						<xsl:element name="{current-grouping-key()}">
							<xsl:value-of select="replace($val,'^no_','is_')"/>
						</xsl:element>
					</xsl:when>
					<xsl:when test="matches($val,'^(is|has)_')">
						<xsl:element name="{current-grouping-key()}">
							<xsl:value-of select="concat('no_',replace($val,'^(is|has)_',''))"/>
						</xsl:element>
					</xsl:when>
					<xsl:when test="matches($val,'^[a-z]')">
						<xsl:element name="{current-grouping-key()}">
							<xsl:value-of select="concat('no_',upper-case(substring($val,1,1)),substring($val,2))"/>
						</xsl:element>
					</xsl:when>
					<xsl:otherwise>
						<xsl:element name="{current-grouping-key()}">
							<xsl:value-of select="concat('no_',lower-case(substring($val,1,1)),substring($val,2))"/>
						</xsl:element>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:for-each>
		</xsl:for-each-group>
		<rest>
			<xsl:copy-of select="f:pruneEssence($tree,'0',(),0)"/>
		</rest>
	</xsl:function>
	<!-- translate the syntax tree to Pseudocode -->
	<xsl:function name="f:pseudoEssence" as="xs:string">
		<xsl:param name="in" as="item()*"/>
		<xsl:value-of select="f:pseudoEssence($in,0)"/>
	</xsl:function>
	<xsl:function name="f:pseudoEssence" as="xs:string">
		<xsl:param name="in" as="item()*"/>
		<xsl:param name="prio" as="xs:integer"/>
		<xsl:variable name="pre" select="if ($in/@prio &lt; $prio) then '(' else ''"/>
		<xsl:variable name="post" select="if ($in/@prio &lt; $prio) then ')' else ''"/>
		<xsl:choose>
			<xsl:when test="$in/@kind='not'">
				<xsl:variable name="complement" as="xs:string">
					<xsl:choose>
						<xsl:when test="$in/*[1]/@kind = 'gt'">le</xsl:when>
						<xsl:when test="$in/*[1]/@kind = 'lt'">ge</xsl:when>
						<xsl:when test="$in/*[1]/@kind = 'ge'">lt</xsl:when>
						<xsl:when test="$in/*[1]/@kind = 'le'">gt</xsl:when>
						<xsl:when test="$in/*[1]/@kind = 'eq'">ne</xsl:when>
						<xsl:when test="$in/*[1]/@kind = 'ne'">eq</xsl:when>
						<xsl:when test="$in/*[1]/@kind = 'ma'">nm</xsl:when>
						<xsl:when test="$in/*[1]/@kind = 'nm'">ma</xsl:when>
						<xsl:otherwise>
							<xsl:value-of select="''"/>
						</xsl:otherwise>
					</xsl:choose>
				</xsl:variable>
				<xsl:choose>
					<xsl:when test="string-length($complement)">
						<xsl:variable name="negate" as="item()*">
							<copy>
								<xsl:attribute name="kind" select="$complement"/>
								<xsl:copy-of select="$in/*[1]/@*[local-name()!='kind']|$in/*[1]/*"/>
							</copy>
						</xsl:variable>
						<xsl:value-of select="f:pseudoEssence($negate,$prio)"/>
					</xsl:when>
					<xsl:when test="$in/*[1]/@kind = 'and'">
						<xsl:variable name="negate" as="item()*">
							<copy>
								<xsl:attribute name="kind" select="'or'"/>
								<xsl:copy-of select="$in/*[1]/@*[local-name()!='kind']"/>
								<op>
									<xsl:copy-of select="$in/@*"/>
									<xsl:copy-of select="$in/*[1]/*[1]"/>
								</op>
								<op>
									<xsl:copy-of select="$in/@*"/>
									<xsl:copy-of select="$in/*[1]/*[2]"/>
								</op>
							</copy>
						</xsl:variable>
						<xsl:value-of select="f:pseudoEssence($negate,$prio)"/>
					</xsl:when>
					<xsl:when test="$in/*[1]/@kind = 'or'">
						<xsl:variable name="negate" as="item()*">
							<copy>
								<xsl:attribute name="kind" select="'and'"/>
								<xsl:copy-of select="$in/*[1]/@*[local-name()!='kind']"/>
								<op>
									<xsl:copy-of select="$in/@*"/>
									<xsl:copy-of select="$in/*[1]/*[1]"/>
								</op>
								<op>
									<xsl:copy-of select="$in/@*"/>
									<xsl:copy-of select="$in/*[1]/*[2]"/>
								</op>
							</copy>
						</xsl:variable>
						<xsl:value-of select="f:pseudoEssence($negate,$prio)"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="concat('not ',$pre,f:pseudoEssence($in/*[1],$in/@prio),$post)"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='and'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' &amp;amp;&amp;amp; ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='or'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' || ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='ge'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' &amp;gt;= ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='le'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' &amp;lt;= ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='gt'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' &amp;gt; ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='lt'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' &amp;lt; ', f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='eq'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' == ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='ne'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' != ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='nm'">
				<xsl:value-of select="concat('not contains(',f:pseudoEssence($in/*[1],$in/@prio),', ',f:pseudoEssence($in/*[2],$in/@prio),')')"/>
			</xsl:when>
			<xsl:when test="$in/@kind='ma'">
				<xsl:value-of select="concat('contains(',f:pseudoEssence($in/*[1],$in/@prio),', ',f:pseudoEssence($in/*[2],$in/@prio),')')"/>
			</xsl:when>
			<xsl:when test="$in/@kind='add'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' + ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='cat'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' &amp;amp; ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='sub'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' - ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mul'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' * ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='div'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' div ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='mod'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' mod ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='exp'">
				<xsl:value-of select="concat($pre,f:pseudoEssence($in/*[1],$in/@prio),' ^ ',f:pseudoEssence($in/*[2],$in/@prio),$post)"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const' and $in/@type='string'">
				<xsl:value-of select="concat('&quot;',replace($in/text(),'&quot;','\\&quot;'),'&quot;')"/>
			</xsl:when>
			<xsl:when test="$in/@kind='const'">
				<xsl:choose>
					<xsl:when test="$in/text() castable as xs:integer and xs:integer($in/text()) &gt; 15">
						<xsl:value-of select="concat('0x',f:decimal-to-hex($in/text()))"/>
					</xsl:when>
					<xsl:otherwise>
						<xsl:value-of select="$in/text()"/>
					</xsl:otherwise>
				</xsl:choose>
			</xsl:when>
			<xsl:when test="$in/@kind='var'">
				<xsl:value-of select="$in/text()"/>
			</xsl:when>
			<xsl:when test="$in/@kind='func'">
				<xsl:variable name="res" as="xs:string*">
					<xsl:for-each select="$in/*[position()!=1]">
						<xsl:sequence select="f:pseudoEssence(.,0)"/>
					</xsl:for-each>
				</xsl:variable>
				<xsl:value-of select="concat($pre,$in/*[1]/text(),'(',string-join($res,','),')',$post)"/>
			</xsl:when>
			<xsl:otherwise>
				<xsl:message terminate="yes">ERROR: Undefined expression operator "<xsl:value-of select="$in/@kind"/>" !</xsl:message>
			</xsl:otherwise>
		</xsl:choose>
	</xsl:function>
	<!-- <xsl:message terminate="no">Before: <xsl:value-of select="$in"/>After: <xsl:value-of select="$patched"/></xsl:message> -->
	<!--		-->
	<!--	====================================================================	-->
	<!--		Decimal  to  Binary Function		========================================== 	-->
	<!--		-->
	<!-- xsl:function name="f:decimal-to-bin" as="xs:string">
		<xsl:param name="decimalNumber"/>
		<xsl:variable name="upperDigits">
			<xsl:if test="$decimalNumber &gt;= 2">
				<xsl:sequence select="string-join(f:decimal-to-bin(floor($decimalNumber div 2)), '')"/>
			</xsl:if>
		</xsl:variable>
		<xsl:sequence select="string-join(($upperDigits,string($decimalNumber mod 2)), '')"/>
	</xsl:function -->
	<xsl:function name="f:decimal-to-bin" as="xs:string">
		<xsl:param name="decimalNumber"/>
		<xsl:sequence select="string-join(reverse(f:decimal-to-bin-h($decimalNumber)), '')"/>
	</xsl:function>
	<xsl:function name="f:decimal-to-bin-h" as="xs:string*">
		<xsl:param name="decimalNumber"/>
		<xsl:sequence select="string($decimalNumber mod 2)"/>
		<xsl:if test="$decimalNumber &gt;= 2">
				<xsl:sequence select="f:decimal-to-bin-h($decimalNumber idiv 2)"/>
		</xsl:if>
	</xsl:function>
	<!--		-->
	<!--	====================================================================	-->
	<!--		Decimal  to  Hex Function		============================================ 	-->
	<!--		-->
	<xsl:function name="f:decimal-to-hex" as="xs:string">
		<xsl:param name="decimalNumber"/>
		<xsl:variable name="hexDigits" select="'0123456789ABCDEF'"/>
		<xsl:variable name="upperDigits">
			<xsl:if test="$decimalNumber &gt;= 16">
				<xsl:sequence select="string-join(f:decimal-to-hex(floor($decimalNumber div 16)), '')"/>
			</xsl:if>
		</xsl:variable>
		<xsl:sequence select="string-join(($upperDigits,substring($hexDigits, ($decimalNumber mod 16) + 1, 1)), '')"/>
	</xsl:function>
</xsl:stylesheet>
