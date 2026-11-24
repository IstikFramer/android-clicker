extends Control

func _ready() -> void:
	$Sky.material.set_shader_parameter("quality_level",Settings.values.quality)
	%Start.pressed.connect(SceneRouter.show_world)
	%SettingsButton.pressed.connect(SceneRouter.show_settings)
	%Credits.pressed.connect(SceneRouter.show_credits)
	%Exit.pressed.connect(get_tree().quit)
	%Start.grab_focus()
