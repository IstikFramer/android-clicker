extends SceneTree

func _initialize() -> void:
	run.call_deferred()

func run() -> void:
	if change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene")) != OK:
		push_error("Main scene failed to load")
		quit(1)
		return
	await scene_changed
	root.add_child(load("res://tests/test_application.gd").new())
