extends Control

func _ready() -> void:
	%Back.pressed.connect(SceneRouter.show_menu)
	%Back.grab_focus()
