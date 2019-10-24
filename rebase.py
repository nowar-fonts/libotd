def ScaleGlyph(glyph, scale, r):
	glyph['advanceWidth'] = r(glyph['advanceWidth'] * scale)
	if 'advanceHeight' in glyph:
		glyph['advanceHeight'] = r(glyph['advanceHeight'] * scale)
		glyph['verticalOrigin'] = r(glyph['verticalOrigin'] * scale)
	rm = [ 'stemH', 'stemV', 'hintMasks', 'contourMasks', 'instructions' ]
	for k in rm:
		if k in glyph:
			del glyph[k]
	if 'contours' in glyph:
		for contour in glyph['contours']:
			for point in contour:
				point['x'] = r(point['x'] * scale)
				point['y'] = r(point['y'] * scale)
	if 'references' in glyph:
		for reference in glyph['references']:
			reference['x'] = r(reference['x'] * scale)
			reference['y'] = r(reference['y'] * scale)

def ScaleMarkToBase(subtable, scale, r):
	for _, mark in subtable['marks'].items():
		mark['x'] = r(mark['x'] * scale)
		mark['y'] = r(mark['y'] * scale)
	for _, base in subtable['bases'].items():
		for _, klass in base.items():
			klass['x'] = r(klass['x'] * scale)
			klass['y'] = r(klass['y'] * scale)

def ScaleMarkToLig(subtable, scale, r):
	for _, mark in subtable['marks'].items():
		mark['x'] = r(mark['x'] * scale)
		mark['y'] = r(mark['y'] * scale)
	for _, base in subtable['bases'].items():
		for component in base:
			for _, klass in component.items():
				klass['x'] = r(klass['x'] * scale)
				klass['y'] = r(klass['y'] * scale)

def ScaleGposValue(entry, scale, r):
	optional = lambda d, k: d[k] if k in d else 0
	return {
		k: r(optional(entry, k) * scale)
		for k in [ 'dx', 'dy', 'dWidth', 'dHeight' ]
	}

def ScaleGposSingle(subtable, scale, r):
	for k, v in subtable.items():
		subtable[k] = ScaleGposValue(v, scale, r)

def ScaleGposPair(subtable, scale, r):
	for row in subtable['matrix']:
		for j in range(len(row)):
			if type(row[j]) in [ int, float ]:
				row[j] = r(row[j] * scale)
			else:
				if 'first' in row[j]:
					row[j]['first'] = ScaleGposValue(row[j]['first'], scale, r)
				if 'second' in row[j]:
					row[j]['second'] = ScaleGposValue(row[j]['second'], scale, r)

GposScaler = {
	'gpos_mark_to_base': ScaleMarkToBase,
	'gpos_mark_to_mark': ScaleMarkToBase,
	'gpos_mark_to_ligature': ScaleMarkToLig,
	'gpos_single': ScaleGposSingle,
	'gpos_pair': ScaleGposPair,
}

def Rebase(font, scale, roundToInt = False):
	r = round if roundToInt else lambda x: x
	if scale == 1:
		return
	for _, g in font['glyf'].items():
		ScaleGlyph(g, scale, r)
	font['head']['unitsPerEm'] = r(font['head']['unitsPerEm'] * scale)

	if 'hhea' in font:
		s = [ 'ascender', 'descender', 'lineGap' ]
		for k in s:
			font['hhea'][k] = r(font['hhea'][k] * scale)

	if 'vhea' in font:
		s = [ 'ascent', 'descent', 'lineGap' ]
		for k in s:
			font['vhea'][k] = r(font['vhea'][k] * scale)

	if 'OS_2' in font:
		s = [
			'xAvgCharWidth', 'usWinAscent', 'usWinDescent', 'sTypoAscender', 'sTypoDescender', 'sTypoLineGap', 'sxHeight', 'sCapHeight',
			'ySubscriptXSize', 'ySubscriptYSize', 'ySubscriptXOffset', 'ySubscriptYOffset',
			'ySupscriptXSize', 'ySupscriptYSize', 'ySupscriptXOffset', 'ySupscriptYOffset', 'yStrikeoutSize', 'yStrikeoutPosition',
		]
		for k in s:
			font['OS_2'][k] = r(font['OS_2'][k] * scale)

	if 'post' in font:
		s = [ 'underlinePosition', 'underlineThickness' ]
		for k in s:
			font['post'][k] = r(font['post'][k] * scale)

	if 'GPOS' in font:
		for _, lookup in font['GPOS']['lookups'].items():
			if lookup['type'] in GposScaler:
				scaler = GposScaler[lookup['type']]
				for subtable in lookup['subtables']:
					scaler(subtable, scale, r)
