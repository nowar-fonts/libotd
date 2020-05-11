kvfilter = lambda d, f: {k: v for k, v in d.items() if f(k, v)}

# tag can be str or list
def RemoveFeature(table, tag):
	rm = []
	for f in table['features']:
		if f[0:4] in tag:
			rm.append(f)
	for f in rm:
		del table['features'][f]

def SubsetLayoutLanguage(table, tag):
	rm = []
	for l in table['languages']:
		if l[5:9] not in tag:
			rm.append(l)
	for l in rm:
		del table['languages'][l]

def SubsetLayoutScript(table, tag):
	rm = []
	for l in table['languages']:
		if l[0:4] not in tag:
			rm.append(l)
	for l in rm:
		del table['languages'][l]

def NowarRemoveFeatures(asianFont):
	RemoveFeature(asianFont['GSUB'], [ 'locl', 'pwid', 'fwid', 'hwid', 'twid', 'qwid', 'vert', 'vrt2', 'aalt' ])
	RemoveFeature(asianFont['GPOS'], [ 'palt', 'halt', 'vert', 'vpal', 'vhal', 'vkrn' ])

def FiltFeature(table):
	visibleLanguages = set()
	visibleFeatures = set()
	visibleLookups = set()
	for lid, lang in table['languages'].items():
		if not lang:
			continue
		visibleLanguages.add(lid)
		if 'requiredFeature' in lang and lang['requiredFeature'] in table['features']:
			visibleFeatures.add(lang['requiredFeature'])
		if 'features' not in lang or not lang['features']:
			lang['features'] = []
		for f in lang['features']:
			if f in table['features'] and table['features'][f]:
				visibleFeatures.add(f)
	table['languages'] = kvfilter(table['languages'], lambda k, _: k in visibleLanguages)
	table['features'] = kvfilter(table['features'], lambda k, _: k in visibleFeatures)

	for _, lutids in table['features'].items():
		for lutid in lutids:
			if lutid in table['lookups'] and table['lookups'][lutid]:
				visibleLookups.add(lutid)

	while True:
		nA = len(visibleLookups)
		for lid, lut in table['lookups'].items():
			if not lut or lid not in visibleLookups:
				continue
			if lut['type'] in ['gsub_chaining', 'gpos_chaining']:
				for rule in lut['subtables']:
					for application in rule['apply']:
						visibleLookups.add(application['lookup'])
		nK = len(visibleLookups)
		if nK >= nA:
			break

	table['lookups'] = kvfilter(table['lookups'], lambda k, _ : k in visibleLookups)

def Mark(lut, obj):
	if type(obj) == str:
		lut.add(obj)
	elif type(obj) == list:
		for s in obj:
			Mark(lut, s)
	elif type(obj) == dict:
		for k, v in obj.items():
			Mark(lut, k)
			Mark(lut, v)

def MarkSubtable(lut, type_, st):
	if type_ in ['gsub_single', 'gsub_multi', 'gsub_alternate']:
		for k, v in st.items():
			if k in lut:
				Mark(lut, v)
	elif type_ == 'gsub_ligature':
		for sub in st['substitutions']:
			if all([g in lut for g in sub['from']]):
				Mark(lut, sub['to'])
	elif type_ == 'gsub_chaining':
		pass
	else:
		Mark(lut, st)

def MarkFont(font):
	lut = set()
	while True:
		lutn = len(lut)
		if 'glyph_order' in font:
			Mark(lut, font['glyph_order'][0])
		Mark(lut, font['cmap'])
		if 'cmap_uvs' in font:
			Mark(lut, font['cmap_uvs'])
		if 'GSUB' in font:
			for _, lookup in font['GSUB']['lookups'].items():
				if 'subtables' in lookup:
					for st in lookup['subtables']:
						MarkSubtable(lut, lookup['type'], st)
		lutn1 = len(lut)
		if lutn1 == lutn:
			break

	for _, g in font['glyf'].items():
		if 'references' in g:
			Mark(lut, g['references'])
	return lut

def Gc(font):
	if 'GSUB' in font:
		FiltFeature(font['GSUB'])
	if 'GPOS' in font:
		FiltFeature(font['GPOS'])

	for _ in range(16):
		lut = MarkFont(font)
		glyf_ = font['glyf']
		na = len(glyf_)
		g1 = {}
		for g, d in glyf_.items():
			if g in lut:
				g1[g] = d
		nk = len(g1)
		font['glyf'] = g1
		if nk >= na:
			break

def ConsolidateLookup(lut, font):
	if lut["type"] == "gsub_ligature":
		def consolidateLigature(st):
			result = []
			glyf = font["glyf"]
			for item in st["substitutions"]:
				if all([glyph in glyf for glyph in item["from"]]) and item["to"] in glyf:
					result.append(item)
			return {"substitutions": result}
		lut["subtables"]= [*map(consolidateLigature, lut["subtables"])]

def ConsolidateLayout(table, font):
	for _, lut in table["lookups"].items():
		ConsolidateLookup(lut, font)

def Consolidate(font):
	if "GSUB" in font:
		ConsolidateLayout(font["GSUB"], font)
	if "GPOS" in font:
		ConsolidateLayout(font["GPOS"], font)
