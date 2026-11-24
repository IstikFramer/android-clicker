class_name FragmentPool
extends Node3D

const FRAGMENT := preload("res://scenes/fracture/Fragment.tscn")
const LIMITS := [48,96,160,500]
const GRAVITY := {"g_game":.15,"epsilon":.3,"max_acceleration":3.}
var free_bodies: Array[RigidBody3D] = []
var free_visuals: Array[MeshInstance3D] = []
var physical: Array[Dictionary] = []
var cosmetic: Array[Dictionary] = []
var gravity_clock := 0.0

func prepare(quality: int, count: int) -> void:
	var limit := mini(count,LIMITS[clampi(quality,0,3)])
	for i in limit:
		var body := FRAGMENT.instantiate() as RigidBody3D
		add_child(body)
		free_bodies.append(body)
	for i in count-limit:
		var skin := MeshInstance3D.new()
		skin.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(skin)
		skin.hide()
		free_visuals.append(skin)

func launch(data: FractureData, plan: Dictionary, snapshot: Transform3D, spin_rate: float, eye: Vector3) -> void:
	var order := []
	for k in plan.selected_ids.size():
		var cell: Dictionary = data.cells[plan.selected_ids[k]]
		order.append([k,cell.size / maxf(.01,eye.distance_to(snapshot*cell.center))])
	order.sort_custom(func(a,b): return a[1]>b[1] or (a[1]==b[1] and a[0]<b[0]))
	for entry in order:
		var k: int = entry[0]
		var id: int = plan.selected_ids[k]
		var cell: Dictionary = data.cells[id]
		var transform_at_hit := Transform3D(snapshot.basis,snapshot*cell.center)
		var tangent: Vector3 = snapshot.basis*(Vector3.UP.cross(cell.center)*spin_rate)
		var impulse: Vector3 = snapshot.basis*plan.impulses[k]
		var torque: Vector3 = snapshot.basis*plan.angular_impulses[k]
		var delay := float(plan.breakup_seconds)*float(k)/maxi(1,order.size()-1)
		var life := (8.+float(id%11)) if not plan.annihilate else float(plan.breakup_seconds)+.6
		if not free_bodies.is_empty():
			var body: RigidBody3D = free_bodies.pop_back()
			body.get_node("Skin").mesh = cell.mesh
			body.get_node("Hull").shape = cell.shape
			body.global_transform = transform_at_hit
			body.mass = plan.masses[k]
			body.collision_mask = 0
			body.show()
			physical.append({"body":body,"age":-delay,"tangent":tangent,"impulse":impulse,"torque":torque,"life":life,"acc":Vector3.ZERO,
				"contacts":physical.size()<24,"fading":plan.annihilate})
		elif not free_visuals.is_empty():
			var visual: MeshInstance3D = free_visuals.pop_back()
			visual.mesh = cell.mesh
			visual.global_transform = transform_at_hit
			visual.show()
			cosmetic.append({"node":visual,"velocity":tangent+impulse/plan.masses[k],
				"axis":torque.normalized(),"speed":torque.length()/plan.masses[k],
				"age":-delay,"life":life,"fading":plan.annihilate})

func release_body(item: Dictionary) -> void:
	var body: RigidBody3D = item.body
	body.freeze = true
	body.collision_layer = 0
	body.collision_mask = 0
	body.get_node("Hull").disabled = true
	body.get_node("Skin").scale = Vector3.ONE
	body.get_node("Skin").mesh = null
	body.get_node("Hull").shape = null
	body.hide()
	free_bodies.append(body)

func release_visual(item: Dictionary) -> void:
	var node: MeshInstance3D = item.node
	node.mesh = null
	node.hide()
	node.scale = Vector3.ONE
	free_visuals.append(node)

func clear() -> void:
	for item in physical: release_body(item)
	for item in cosmetic: release_visual(item)
	physical.clear()
	cosmetic.clear()
	gravity_clock = 0.

func _physics_process(delta: float) -> void:
	if GameState.director.state == ShotDirector.State.PAUSED: return
	gravity_clock -= delta
	if gravity_clock<=0. and not physical.is_empty():
		gravity_clock = 1./12.
		var positions := PackedVector3Array()
		var masses := PackedFloat32Array()
		var subset := []
		for item in physical:
			item.acc = Vector3.ZERO
			var body: RigidBody3D = item.body
			if subset.size()<96 and not body.freeze and not body.sleeping and body.position.length_squared()<6400.:
				subset.append(item)
				positions.append(body.position)
				masses.append(body.mass)
		var acc: PackedVector3Array = CountryLookup.geometry.gravity_step(positions,masses,GRAVITY)
		for i in acc.size(): subset[i].acc = acc[i]
	for i in range(physical.size()-1,-1,-1):
		var item := physical[i]
		var body: RigidBody3D = item.body
		item.age += delta
		if item.age<0.: continue
		if body.freeze:
			body.get_node("Hull").disabled=false
			body.freeze=false
			body.sleeping=false
			body.linear_velocity=item.tangent
			body.angular_velocity=Vector3.ZERO
			body.apply_central_impulse(item.impulse)
			body.apply_torque_impulse(item.torque)
		if item.age>=item.life:
			release_body(item)
			physical.remove_at(i)
			continue
		if item.contacts and item.age>=.23 and body.collision_layer==0:
			body.collision_layer = 4
			body.collision_mask = 4
		if not body.sleeping: body.apply_central_force(item.acc*body.mass)
		if item.fading: body.get_node("Skin").scale=Vector3.ONE*maxf(.001,1.-item.age/item.life)
	for i in range(cosmetic.size()-1,-1,-1):
		var item := cosmetic[i]
		item.age += delta
		if item.age<0.: continue
		if item.age >= item.life:
			release_visual(item)
			cosmetic.remove_at(i)
			continue
		var node: MeshInstance3D = item.node
		node.position += item.velocity*delta
		if item.speed>.001: node.rotate(item.axis,item.speed*delta)
		if item.fading: node.scale = Vector3.ONE*maxf(.001,1.-item.age/item.life)
