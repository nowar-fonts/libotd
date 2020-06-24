##
## simple merger: merge glyphs and ignore all OpenType layout features
##

def AddRef(n, font, ref):
	if n in ref:
		return
	glyph = font['glyf'][n]
	if 'references' in glyph:
		for r in glyph['references']:
			ref.append(r['glyph'])
			AddRef(r['glyph'], font, ref)

def TrimGlyph(font):
	needed = []
	for (_, n) in font['cmap'].items():
		needed.append(n)
	ref = []
	for n in needed:
		AddRef(n, font, ref)

	unneeded = []
	for n in font['glyf']:
		if not (n in needed or n in ref):
			unneeded.append(n)
	for n in unneeded:
		del font['glyf'][n]

def CopyRef(glyph, a, b):
	if 'references' in glyph:
		for r in glyph['references']:
			if r['glyph'] not in a['glyf']:
				a['glyf'][r['glyph']] = b['glyf'][r['glyph']]
				CopyRef(a['glyf'][r['glyph']], a, b)

def MergeSimple(base, ext):
	for u, n in ext['cmap'].items():
		if u not in base['cmap'].keys():
			base['cmap'][u] = n
			if n not in base['glyf'].keys():
				glyph = ext['glyf'][n]
				base['glyf'][n] = glyph
				CopyRef(glyph, base, ext)

##
## Megaminx’s merging algorithm: merge glyphs and keep OpenType layout features
##

def MergeLayout(base, ext, preferExt = False):
	for fid, value in ext['features'].items():
		base['features'][fid] = value
	for lid, value in ext['lookups'].items():
		base['lookups'][lid] = value

	for lid, value in ext['languages'].items():
		if lid in base['languages']:
			base['languages'][lid]['features'] += ext['languages'][lid]['features']
		else:
			base['languages'][lid] = ext['languages'][lid]

	def l(f, s):
		lookupOrder = []
		if 'lookupOrder' in f:
			lookupOrder += f['lookupOrder']
		if 'lookupOrder' in s:
			lookupOrder += s['lookupOrder']
		return lookupOrder
	base['lookupOrder'] = l(ext, base) if preferExt else l(base, ext)

def MergeGdef(first, second):
	def m(k):
		result = {}
		if k in second:
			result.update(second)
		if k in first:
			result.update(first)
	return { k: m(k) for k in [ 'markAttachClassDef', 'glyphClassDef', 'ligCarets' ] }

# base and ext must have diffefent prefixes
def MergeBelow(base, ext, mergeLayout = True):
	for k, v in ext['cmap'].items():
		if k not in base['cmap']:
			base['cmap'][k] = v
	if 'cmap_uvs' in ext:
		if 'cmap_uvs' not in base:
			base['cmap_uvs'] = {}
		for k, v in ext['cmap_uvs'].items():
			if k not in base['cmap_uvs']:
				base['cmap_uvs'][k] = v

	base['glyf'].update(ext['glyf'])

	if mergeLayout:
		if 'GSUB' in ext:
			if 'GSUB' in base:
				MergeLayout(base['GSUB'], ext['GSUB'])
			else:
				base['GSUB'] = ext['GSUB']
		if 'GPOS' in ext:
			if 'GPOS' in base:
				MergeLayout(base['GPOS'], ext['GPOS'])
			else:
				base['GPOS'] = ext['GPOS']
		if 'GDEF' in ext:
			if 'GDEF' in base:
				MergeGdef(base['GDEF'], ext['GDEF'])
			else:
				base['GDEF'] = ext['GDEF']

# base and ext must have diffefent prefixes
def MergeAbove(base, ext, mergeLayout = True):
	gid0 = ext['glyph_order'][0]
	for k, v in ext['cmap'].items():
		if int(k) > 0x20 and v != gid0:
			base['cmap'][k] = v
	if 'cmap_uvs' in ext:
		if 'cmap_uvs' not in base:
			base['cmap_uvs'] = {}
		for k, v in ext['cmap_uvs'].items():
			if v != gid0:
				base['cmap_uvs'][k] = v

	base['glyf'].update({ k: v for k, v in ext['glyf'].items() if k != gid0 })

	if mergeLayout:
		if 'GSUB' in ext:
			if 'GSUB' in base:
				MergeLayout(base['GSUB'], ext['GSUB'], preferExt = True)
			else:
				base['GSUB'] = ext['GSUB']
		if 'GPOS' in ext:
			if 'GPOS' in base:
				MergeLayout(base['GPOS'], ext['GPOS'], preferExt = True)
			else:
				base['GPOS'] = ext['GPOS']
		if 'GDEF' in ext:
			if 'GDEF' in base:
				MergeGdef(ext['GDEF'], base['GDEF'])
			else:
				base['GDEF'] = ext['GDEF']
