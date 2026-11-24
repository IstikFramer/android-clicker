extends Node

func _ready() -> void:
	SceneRouter.attach($SceneHost, $LoadingOverlay)
	# Release templates run package verification through the normal entry point.
	if "--verify-package" in OS.get_cmdline_user_args():
		add_child(load("res://tests/test_application.gd").new())
