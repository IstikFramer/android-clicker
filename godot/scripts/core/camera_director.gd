extends Node3D

@onready var camera: Camera3D = $Camera3D

func _ready() -> void:
	camera.make_current()

func reset_view() -> void:
	rotation = Vector3.ZERO
	camera.position.z = 5.9

func _unhandled_input(event: InputEvent) -> void:
	if GameState.director.state != ShotDirector.State.IDLE:
		return
	if event is InputEventMouseMotion and Input.is_action_pressed("orbit_drag"):
		rotation.y -= event.relative.x * 0.005
		rotation.x = clampf(rotation.x - event.relative.y * 0.005, -1.4, 1.4)
	elif event.is_action_pressed("zoom_in"):
		camera.position.z = maxf(camera.position.z - 0.4, 3.6)
	elif event.is_action_pressed("zoom_out"):
		camera.position.z = minf(camera.position.z + 0.4, 10.0)
