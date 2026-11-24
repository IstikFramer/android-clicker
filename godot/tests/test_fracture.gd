extends RefCounted

func check(world: Node, expect: Callable) -> void:
	var tree:=world.get_tree()
	var settings:=world.get_node("/root/Settings")
	var options: Dictionary=settings.values.duplicate()
	options.quality=0
	settings.apply(options)
	world.choose_weapon(&"railgun")
	world.choose_target(&"earth")
	var start:=Time.get_ticks_usec()
	var prepared: bool=world.prepare_fracture()
	expect.call(prepared,"offline Earth partition")
	if not prepared: return
	var f: FractureController=world.fracture
	var pool:=f.pool
	var budget:=pool.get_child_count()
	var loaded:=(Time.get_ticks_usec()-start)/1000.
	var first_ids: PackedInt32Array
	var longest:=0.
	for i in 20:
		start=Time.get_ticks_usec()
		var direction:=Vector3(.77,.26,.58).normalized()
		var result: Dictionary=world.demo_hit(direction,50 if i==0 else 100)
		longest=maxf(longest,(Time.get_ticks_usec()-start)/1000.)
		expect.call(result.get("ok",false),"stress impact %d"%i)
		if result.is_empty(): return
		expect.call(pool.physical.size()==48 and pool.get_child_count()==budget,"low body and node budget")
		expect.call(pool.physical.size()+pool.cosmetic.size()==result.selected_ids.size(),"every cell has its visual")
		if i==0:
			first_ids=result.selected_ids
			expect.call(f.remnant.mesh.get_surface_count()==2 and not world.planet.surface_mesh.visible,"open remnant with capped interior")
			var item: Dictionary=pool.physical[0]
			var body: RigidBody3D=item.body
			var initial:=body.global_position
			for frame in 42: await tree.physics_frame
			expect.call(not body.freeze and body.linear_velocity.length()>.01 and initial.distance_to(body.global_position)>.002,"Jolt integrated real impulse")
			var second: Dictionary=world.demo_hit(-direction,100)
			expect.call(second.get("destroyed",false) and second.selected_ids.size()+first_ids.size()==480,"second hit removes remaining mass")
		expect.call(f.remnant.mesh==null and f.population==0 and f.integrity==0.,"full destruction has no solid survivor")
		f.restore()
		expect.call(pool.physical.is_empty() and pool.cosmetic.is_empty() and pool.free_bodies.size()==48,"reset recycles full pool")
		expect.call(f.data.rows.all(func(row):return not row.active) and f.population==8000000000 and f.integrity==1.,"reset original mass and population")
		expect.call(f.remnant.mesh.get_surface_count()==1 and pool.get_child_count()==budget,"bounded nodes across resets")
	print("FRACTURE STRESS PASS cycles=20 nodes=",budget," low_physics=48 load_ms=",loaded," peak_hit_ms=",longest)
	for quality in [1,2,3]:
		world.restore_target()
		options.quality=quality
		settings.apply(options)
		world.choose_target(&"earth")
		if not world.prepare_fracture():
			expect.call(false,"quality cache")
			return
		var result: Dictionary=world.demo_hit(Vector3(.77,.26,.58).normalized(),100)
		expect.call(result.get("integrity",-1)==0 and result.selected_ids.size()==480,"presets preserve mass")
		expect.call(world.fracture.pool.physical.size()==mini(FragmentPool.LIMITS[quality],480),"preset rigid budget %d"%quality)
	world.demo_power=20
	world.choose_target(&"mars")
	var martian: Dictionary=world.demo_hit(Vector3.RIGHT,20)
	expect.call(martian.get("integrity",1.)<1.,"Mars crust")
	world.choose_target(&"venus")
	var venus: Dictionary=world.demo_hit(Vector3.UP,10)
	expect.call(venus.get("crater_radius_game_km",0.)>0.,"Venus crater")
	world.choose_target(&"mars")
	expect.call(is_equal_approx(world.fracture.integrity,martian.integrity),"returning to a damaged target")
	world.get_node("/root/GameState").reset_world()
	expect.call(world.fracture.integrity==1. and world.fracture.pool.physical.is_empty(),"reset restores selected planet")
	world.choose_target(&"mercury")
	var mercury: Dictionary=world.demo_hit(Vector3.RIGHT,20)
	expect.call(mercury.get("damage_fraction",0.)>.08 and world.fracture.atmosphere==0.,"Mercury resistance and vacuum")
	world.demo_power=0
	world.choose_weapon(&"gungnir")
	world.choose_target(&"saturn")
	if not world.prepare_fracture():
		expect.call(false,"gas path")
		return
	var gas: Dictionary=world.demo_hit(Vector3.RIGHT,100)
	expect.call(gas.get("status_key","")=="gas_dispersed" and gas.crater_radius_game_km==0 and gas.selected_ids.is_empty(),"gas dispersion")
	world.fracture.skip()
	expect.call(not world.planet.surface_mesh.visible and not world.planet.get_node("SpinPivot/RingSystem").visible,"dispersed rings")
	world.choose_weapon(&"vera")
	world.choose_target(&"sun")
	if not world.prepare_fracture():
		expect.call(false,"stellar path")
		return
	var solar: Dictionary=world.demo_hit(Vector3.UP,20)
	expect.call(solar.get("status_key","")=="solar_impact" and solar.selected_ids.is_empty(),"stellar interface")
	var rows: Array[Dictionary]=[{"id":0}]
	var bad:=CountryLookup.geometry.plan_impact(rows,{})
	expect.call(not bad.ok and not bad.error.is_empty(),"invalid variant returns an error")
