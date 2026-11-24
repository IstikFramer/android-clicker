extends RefCounted

func check(world, expect: Callable) -> void:
	var geometry := CountryLookup.geometry
	for sample in [[24.938,60.17,"FI"],[139.69,35.68,"JP"],[-47.88,-15.79,"BR"],[151.21,-33.87,"AU"],
		[-140,0,"Ocean"],[179.99,65.5,"RU"],[-179.99,65.5,"RU"],[27.48,-29.31,"LS"],[0,90,"Ocean"],[0,-90,"AQ"]]:
		var uv := Vector2(float(sample[0])/360+.5,.5-float(sample[1])/180)
		var direction := geometry.globe_direction(uv)
		expect.call(direction.is_normalized(), "finite unit direction")
		expect.call(CountryLookup.region(direction).code == sample[2],"geography %s" % sample[2])
	expect.call(CountryLookup.rows.size() == 242,"pinned Natural Earth catalogue")
	for row: Dictionary in CountryLookup.rows:
		expect.call(CountryLookup.region(CountryLookup.representative(row)).code == row.code,"representative: "+row.code)
	expect.call(TargetRegistry.definition(&"earth").population == 8000000000,"int64 fictional population")
	expect.call(not world.picker.buttons[&"sun"].visible,"Sun hidden for railgun")
	expect.call(not world.picker.buttons.has(&"jupiter"),"Jupiter is decor")
	var list: ItemList = world.countries.get_node("Body/List")
	world.picker.get_node("Body/Region").pressed.emit()
	world.countries.get_node("Body/Search").text = "Tokyo"
	world.countries.filter_rows("Japan")
	expect.call(list.item_count == 1 and list.get_item_metadata(0).code == "JP","searchable localized list")
	list.item_selected.emit(0)
	expect.call(world.current_region.code == "JP" and world.rig.locked,"picker aims and locks")
	var local: Vector3 = world.planet.local_hit_dir
	var spin: Node3D = world.planet.get_node("SpinPivot")
	var cam: Camera3D = world.rig.camera
	var projected := cam.unproject_position(spin.to_global(local*10))
	world.pick_screen(projected)
	expect.call(world.planet.local_hit_dir.dot(local) > .99999 and world.current_region.code == "JP","camera projection and inverse spin agree")
	world.lock_button.pressed.emit()
	var request: ShotRequest = world.confirmed
	expect.call(request != null and request.is_valid() and request.country_id == "JP","locked request")
	var before: Vector3 = world.planet.world_direction(request.local_hit_dir)
	world.planet.advance(4.0,Vector3.UP)
	expect.call(world.planet.world_direction(request.local_hit_dir).distance_to(before) > .001 and request.local_hit_dir.dot(local) > .99999,"stored direction is local")
	var time: float = world.planet.elapsed
	GameState.director.toggle_pause()
	world._process(.5)
	expect.call(world.planet.elapsed == time,"pause freezes shader clock and spin")
	GameState.director.toggle_pause()
	var press := InputEventMouseButton.new()
	press.position = world.picker.global_position + Vector2(12,12)
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	world.get_viewport().push_input(press,true)
	press.pressed = false
	world.get_viewport().push_input(press,true)
	expect.call(world.confirmed == request,"HUD consumes clicks")
	world.pick_screen(Vector2(-10000,-10000))
	expect.call(world.planet.local_hit_dir == Vector3.ZERO and world.confirmed == null,"empty space clears point")
	world.picker.get_node("Body/Weapon").item_selected.emit(2)
	expect.call(world.picker.buttons[&"sun"].visible,"VERA exposes Sun")
	for id: StringName in TargetRegistry.ALL:
		world.picker.buttons[id].pressed.emit()
		expect.call(world.planet.definition.id == id,"scene selection: "+id)
		expect.call(world.planet.get_node("SpinPivot/AimArea").collision_layer == 2,"aim-only layer")
		expect.call(world.planet.surface_mesh.mesh != null,"visible globe")
		if id != &"earth":
			world.select_direction(Vector3.LEFT)
			world.confirm_aim()
			expect.call(world.confirmed != null and world.confirmed.country_id == "","free region on "+id)
		var planet: PlanetController = world.planet
		planet.update_lod(400,2)
		expect.call(planet.detail == 3,"high detail")
		planet.update_lod(255,2)
		expect.call(planet.detail == 3,"LOD hysteresis")
		planet.update_lod(60,2)
		expect.call(planet.detail == 1,"distant active target")
		planet.set_destroyed(true)
		expect.call(not planet.get_node("SpinPivot").visible and planet.get_node("SpinPivot/AimArea").collision_layer == 0,"hidden destroyed shell")
		planet.set_destroyed(false)
	world.choose_weapon(&"railgun")
	expect.call(world.planet.definition.id != &"sun","illegal target replaced when switching")
	for id in [&"gungnir",&"vera",&"railgun"]:
		world.choose_weapon(id)
		world.toggle_station()
		expect.call(world.station.visible and not world.planet.visible,"launch viewpoint")
		world.toggle_station()
	for body: PlanetController in world.get_node("Backdrop").get_children():
		expect.call(body.detail == 0 and not body.has_node("SpinPivot/AimArea"),"fixed low-detail nonphysical backdrop")
	world.choose_target(&"earth")
