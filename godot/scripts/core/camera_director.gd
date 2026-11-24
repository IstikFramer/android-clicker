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
var rear_mode:=false
var platform_scale:=.66
var velocity:=Vector3.ZERO
var kick:=0.
var shake_age:=0.
var shake_seed:=0
var rail: Node3D
var target_point:=Vector3.ZERO

func _ready() -> void:
	camera.make_current()
	place()

func frame(center: Vector3, radius: float, generation: int, start_direction: Vector3) -> void:
	token = generation
	focus = center
	locked = false
	min_distance = radius*1.48
	max_distance = radius*8.2
	distance = radius*(3.12 if rear_mode else 3.65)
	clear_shake()
	camera.fov=60. if rear_mode else 44.
	camera.h_offset = -radius*.20 if rear_mode else -radius*.32
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
	if rear_mode and is_instance_valid(rail):
		position_rear(0.,true)
		return
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

func set_rear(platform: Node3D, enabled: bool) -> void:
	rail=platform
	rear_mode=enabled
	velocity=Vector3.ZERO
	target_point=focus

func position_rear(dt: float, snap:=false, orient_platform:=true) -> void:
	if not is_instance_valid(rail): return
	var outward:=Vector3(cos(azimuth)*cos(elevation),sin(elevation),sin(azimuth)*cos(elevation))
	var orbit_basis:=Basis.looking_at(-outward,Vector3.UP)
	var origin:=focus+outward*distance
	rail.global_position=origin+orbit_basis*Vector3(2.55,-1.74,-6.4)
	var look:=target_point-rail.global_position
	if orient_platform and look.length_squared()>.01:
		var safe_up:=Vector3.UP if absf(look.normalized().dot(Vector3.UP))<.985 else orbit_basis.x
		rail.global_basis=Basis.looking_at(look.normalized(),safe_up).scaled_local(Vector3.ONE*platform_scale)
	var shoulder:=Vector3(-3.65,.54,4.)
	var socket: Vector3=rail.to_local(rail.anchor.global_position)
	var desired:=rail.global_position+rail.global_basis.orthonormalized()*(socket+shoulder)
	if snap:
		global_position=desired
		velocity=Vector3.ZERO
	else:
		var lag:=global_position-desired
		var damping:=15.
		var term:=velocity+lag*damping
		var decay:=exp(-damping*dt)
		global_position=desired+(lag+term*dt)*decay
		velocity=(velocity-term*damping*dt)*decay
	var camera_look:=(focus-global_position).normalized()
	var up:=Vector3.UP if absf(camera_look.y)<.99 else orbit_basis.x
	global_basis=Basis.looking_at(camera_look,up)

func shake(amplitude: float, seed_value: int) -> void:
	kick=minf(.31,amplitude)*(.14 if Settings.values.reduced_motion else 1.)
	shake_age=0.
	shake_seed=seed_value%997

func tick_shake(dt: float) -> void:
	if kick<=0.: return
	shake_age+=dt
	var envelope:=kick*exp(-7.*shake_age)
	camera.position=Vector3(sin(47.*shake_age+shake_seed),cos(38.*shake_age+shake_seed),0.)*envelope
	camera.rotation=Vector3(sin(32.*shake_age),cos(43.*shake_age),0.)*envelope*.026
	if shake_age>.74: clear_shake()

func clear_shake() -> void:
	kick=0.
	if camera:
		camera.position=Vector3.ZERO
		camera.rotation=Vector3.ZERO
