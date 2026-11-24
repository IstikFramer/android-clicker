extends Control

func _ready() -> void:
	%Start.pressed.connect(SceneRouter.show_world)
	%SettingsButton.pressed.connect(SceneRouter.show_settings)
	%Credits.pressed.connect(SceneRouter.show_credits)
	%Exit.pressed.connect(get_tree().quit)
	%Start.grab_focus()
