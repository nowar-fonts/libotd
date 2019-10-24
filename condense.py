def CondenseGlyph(glyph, scale, r):
	glyph['advanceWidth'] = r(glyph['advanceWidth'] * scale)
	rm = [ 'stemH', 'stemV', 'hintMasks', 'contourMasks', 'instructions' ]
	for k in rm:
		if k in glyph:
			del glyph[k]
	if 'contours' in glyph:
		for contour in glyph['contours']:
			for point in contour:
				point['x'] = r(point['x'] * scale)
	if 'references' in glyph:
		for reference in glyph['references']:
			reference['x'] = r(reference['x'] * scale)

def CondenseMarkToBase(subtable, scale, r):
	for _, mark in subtable['marks'].items():
		mark['x'] = r(mark['x'] * scale)
	for _, base in subtable['bases'].items():
		for _, klass in base.items():
			klass['x'] = r(klass['x'] * scale)

def CondenseMarkToLig(subtable, scale, r):
	for _, mark in subtable['marks'].items():
		mark['x'] = r(mark['x'] * scale)
	for _, base in subtable['bases'].items():
		for component in base:
			for _, klass in component.items():
				klass['x'] = r(klass['x'] * scale)

def CondenseGposValue(entry, scale, r):
	optional = lambda d, k: d[k] if k in d else 0
	return {
		k: r(optional(entry, k) * scale)
		for k in [ 'dx', 'dWidth' ]
	}

def CondenseGposSingle(subtable, scale, r):
	for k, v in subtable.items():
		subtable[k] = CondenseGposValue(v, scale, r)

def CondenseGposPair(subtable, scale, r):
	for row in subtable['matrix']:
		for j in range(len(row)):
			if type(row[j]) in [ int, float ]:
				# may be bad on `vkrn` table
				row[j] = r(row[j] * scale)
			else:
				if 'first' in row[j]:
					row[j]['first'] = CondenseGposValue(row[j]['first'], scale, r)
				if 'second' in row[j]:
					row[j]['second'] = CondenseGposValue(row[j]['second'], scale, r)

GposCondenser = {
	'gpos_mark_to_base': CondenseMarkToBase,
	'gpos_mark_to_mark': CondenseMarkToBase,
	'gpos_mark_to_ligature': CondenseMarkToLig,
	'gpos_single': CondenseGposSingle,
	'gpos_pair': CondenseGposPair,
}

def Condense(font, scale, roundToInt = False):
	r = round if roundToInt else lambda x: x
	if scale == 1:
		return
	for _, g in font['glyf'].items():
		CondenseGlyph(g, scale, r)

	if 'OS_2' in font:
		s = [ 'xAvgCharWidth', 'ySubscriptXSize', 'ySubscriptXOffset', 'ySupscriptXSize', 'ySupscriptXOffset' ]
		for k in s:
			font['OS_2'][k] = r(font['OS_2'][k] * scale)

	if 'GPOS' in font:
		for _, lookup in font['GPOS']['lookups'].items():
			if lookup['type'] in GposCondenser:
				scaler = GposCondenser[lookup['type']]
				for subtable in lookup['subtables']:
					scaler(subtable, scale, r)
