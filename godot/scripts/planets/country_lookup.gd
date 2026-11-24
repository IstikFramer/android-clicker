class_name CountryLookup
extends RefCounted

static var rows: Array = []
static var by_id: Dictionary = {}
static var by_code: Dictionary = {}
static var mask: Image
static var geometry := FractureBridge.new()

static func initialize() -> void:
	if mask != null:
		return
	var data := FileAccess.get_file_as_bytes("res://data/country_mask.png")
	mask = Image.new()
	if mask.load_png_from_buffer(data) != OK:
		push_error("Cannot decode country_mask.png")
		return
	rows = JSON.parse_string(FileAccess.get_file_as_string("res://data/countries.json"))
	var ocean := {"id": 0, "code": "Ocean", "en": "Ocean", "ru": "Океан", "lon": -140.0, "lat": 0.0}
	for row: Dictionary in [ocean] + rows:
		by_id[int(row.id)] = row
		by_code[row.code] = row

static func region(direction: Vector3) -> Dictionary:
	initialize()
	var uv := geometry.globe_uv(direction)
	if uv.x < 0:
		return {}
	var x := posmod(floori(uv.x * mask.get_width()), mask.get_width())
	var y := clampi(floori(uv.y * mask.get_height()), 0, mask.get_height()-1)
	var pixel := mask.get_pixel(x,y)
	return by_id[pixel.r8 + 256 * pixel.g8]

static func representative(row: Dictionary) -> Vector3:
	return geometry.globe_direction(Vector2(float(row.lon)/360.0+0.5, 0.5-float(row.lat)/180.0))

static func localized(row: Dictionary) -> String:
	return row.ru if TranslationServer.get_locale().begins_with("ru") else row.en
