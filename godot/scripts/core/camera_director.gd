extends Node3D

@onready var camera: Camera3D = $Camera3D
var focus := Vector3.ZERO
var distance := 35.0
var azimuth := 0.48
var elevation := 0.34
var min_distance := 15.0
var max_distance := 76.0
var token := -1
var locked := false

func _ready() -> void:
	camera.make_current()
	place()

func frame(center: Vector3, radius: float, generation: int, start_direction: Vector3) -> void:
	token = generation
	focus = center
	locked = false
	min_distance = radius*1.48
	max_distance = radius*8.2
	distance = radius*3.65
	camera.h_offset = -radius*.32
	orient(start_direction)
	place()

func orient(direction: Vector3) -> void:
	azimuth = atan2(direction.z,direction.x)
	elevation = clampf(asin(clampf(direction.y,-1,1)),-1.565,1.565)

func follow(direction: Vector3, generation: int) -> void:
	if locked and generation == token and token == GameState.director.generation:
		orient(direction)
		place()

func place() -> void:
	var forward := Vector3(cos(azimuth)*cos(elevation),sin(elevation),sin(azimuth)*cos(elevation))
	global_position = focus+forward*distance
	look_at(focus,Vector3.UP)

func _unhandled_input(event: InputEvent) -> void:
	if token != GameState.director.generation or GameState.director.state not in [ShotDirector.State.IDLE,ShotDirector.State.AIM]:
		return
	if event is InputEventMouseMotion and Input.is_action_pressed("orbit_drag"):
		locked = false
		azimuth += event.relative.x*0.005
		elevation = clampf(elevation+event.relative.y*.005,-1.565,1.565)
	elif event.is_action_pressed("zoom_in"):
		distance = maxf(distance/1.13,min_distance)
	elif event.is_action_pressed("zoom_out"):
		distance = minf(distance*1.13,max_distance)
	else:
		return
	place()
	get_viewport().set_input_as_handled()
