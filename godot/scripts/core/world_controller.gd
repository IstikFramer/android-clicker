extends Node3D

func _ready() -> void:
	%Back.pressed.connect(SceneRouter.show_menu)
	EventBus.settings_changed.connect(apply_lighting)
	EventBus.world_reset.connect(on_reset)
	apply_lighting()

func apply_lighting() -> void:
	$KeyLight.shadow_enabled = bool(Settings.values.shadows)

func on_reset(_reset_id: int) -> void:
	$Targets/Sample.rotation = Vector3.ZERO
	$CameraRig.reset_view()
	$HUD/Stack/Paused.hide()

func _process(delta: float) -> void:
	if GameState.director.state == ShotDirector.State.IDLE:
		$Targets/Sample.rotate_y(delta * 0.045)

func _unhandled_key_input(event: InputEvent) -> void:
	if event.is_action_pressed("pause"):
		GameState.director.toggle_pause()
		$HUD/Stack/Paused.visible = GameState.director.state == ShotDirector.State.PAUSED
	elif event.is_action_pressed("reset"):
		GameState.reset_world()
	else:
		return
	get_viewport().set_input_as_handled()
