extends Node

var failures: Array[String] = []

func _ready() -> void:
	run.call_deferred()

func expect(ok: bool, message: String) -> void:
	if not ok:
		failures.append(message)
		push_error(message)

func run() -> void:
	var tree := get_tree()
	var root := tree.root
	expect(ClassDB.class_exists(&"FractureBridge"), "FractureBridge registration")
	if ClassDB.class_exists(&"FractureBridge"):
		var bridge: Object = ClassDB.instantiate(&"FractureBridge")
		expect(bridge.get_api_version() == 1, "bridge API v1")
	expect(ProjectSettings.get_setting("physics/3d/physics_engine") == "Jolt Physics", "Jolt selection")
	await tree.physics_frame
	expect(root.world_3d.direct_space_state.get_class() == "JoltPhysicsDirectSpaceState3D", "running Jolt space")
	for action in ["select","fire","orbit_drag","zoom_in","zoom_out","pause","reset","skip_cinematic","mute"]:
		expect(InputMap.has_action(action) and not InputMap.action_get_events(action).is_empty(), "binding " + action)
	load("res://tests/test_contracts.gd").new().check(expect)
	var settings := root.get_node("Settings")
	var before: Dictionary = settings.values.duplicate()
	var invalid: Dictionary = settings.validated({"fps": -3, "resolution": "big", "language": 10})
	expect(invalid == settings.DEFAULTS, "settings fallback")
	var path := "user://test-settings-%s.cfg" % OS.get_process_id()
	var candidate: Dictionary = settings.DEFAULTS.duplicate()
	candidate.language = 1
	candidate.shadows = 0
	candidate.fps = 0
	expect(settings.save_settings(candidate, path) == OK, "write ConfigFile")
	settings.apply(settings.DEFAULTS)
	settings.load_settings(path)
	expect(settings.values == candidate and Engine.max_fps == 30, "read and apply ConfigFile")
	expect(TranslationServer.translate("START") == &"Start", "English locale")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(path))
	var host := tree.current_scene.get_node("SceneHost")
	expect(host.get_child(0).name == &"MainMenu", "main menu")
	host.get_child(0).get_node("%SettingsButton").pressed.emit()
	expect(host.get_child(0).get_node("%Grid").get_child_count() == 16, "settings controls")
	host.get_child(0).get_node("%Back").pressed.emit()
	host.get_child(0).get_node("%Credits").pressed.emit()
	host.get_child(0).get_node("%Back").pressed.emit()
	host.get_child(0).get_node("%Start").pressed.emit()
	for frame in 4:
		await tree.process_frame
	var world := host.get_child(0)
	expect(world.name == &"SpaceWorld", "menu to world")
	expect(world.get_node("CameraRig/Camera3D").current, "active camera")
	expect(not world.get_node("KeyLight").shadow_enabled, "shadow setting")
	settings.apply(settings.DEFAULTS)
	expect(world.get_node("KeyLight").shadow_enabled, "live shadow change")
	expect(TranslationServer.translate("START") == &"Начать", "Russian locale")
	load("res://tests/test_assets.gd").new().check(expect)
	load("res://tests/test_targeting.gd").new().check(world,expect)
	await load("res://tests/test_fracture.gd").new().check(world,expect)
	var state := root.get_node("GameState")
	state.director.toggle_pause()
	state.reset_world()
	expect(state.director.state == state.director.State.IDLE, "reset releases control")
	world.get_node("%Back").pressed.emit()
	expect(host.get_child(0).name == &"MainMenu", "return to menu")
	settings.apply(before)
	if failures.is_empty():
		print("SPACE DIE SMOKE PASS")
	tree.quit(0 if failures.is_empty() else 1)
