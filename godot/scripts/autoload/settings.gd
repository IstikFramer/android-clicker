extends Node

const PATH := "user://settings.cfg"
const OPTIONS := {
	"resolution": ["1280 × 720", "1600 × 900", "1920 × 1080"],
	"quality": ["LOW", "MEDIUM", "HIGH", "ULTRA"],
	"shadows": ["OFF", "ON"], "particles": ["LOW", "MEDIUM", "HIGH"],
	"vsync": ["OFF", "ON"], "fullscreen": ["OFF", "ON"],
	"fps": ["30", "60", "120", "UNCAPPED"], "language": ["Русский", "English"]
}
const SIZES := [Vector2i(1280, 720), Vector2i(1600, 900), Vector2i(1920, 1080)]
const CAPS := [30, 60, 120, 0]
const DEFAULTS := {"resolution": 2, "quality": 1, "shadows": 1, "particles": 1,
	"vsync": 1, "fullscreen": 0, "fps": 1, "language": 0}
var values := DEFAULTS.duplicate()

func _ready() -> void:
	load_settings(PATH)

func load_settings(path: String) -> void:
	var candidate := DEFAULTS.duplicate()
	var config := ConfigFile.new()
	if config.load(path) == OK:
		for key in DEFAULTS:
			candidate[key] = config.get_value("display", key, DEFAULTS[key])
	apply(candidate)

func validated(candidate: Dictionary) -> Dictionary:
	var result := DEFAULTS.duplicate()
	for key in DEFAULTS:
		var value: Variant = candidate.get(key)
		if typeof(value) == TYPE_INT and value >= 0 and value < OPTIONS[key].size():
			result[key] = value
	return result

func apply(candidate: Dictionary) -> void:
	values = validated(candidate)
	TranslationServer.set_locale(["ru", "en"][values.language])
	Engine.max_fps = CAPS[values.fps]
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if values.fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
		if not values.fullscreen:
			DisplayServer.window_set_size(SIZES[values.resolution])
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if values.vsync else DisplayServer.VSYNC_DISABLED)
	EventBus.settings_changed.emit()

func save_settings(candidate: Dictionary, path: String = PATH) -> Error:
	var sanitized := validated(candidate)
	var config := ConfigFile.new()
	for key in sanitized:
		config.set_value("display", key, sanitized[key])
	var error := config.save(path)
	if error == OK:
		apply(sanitized)
	return error
