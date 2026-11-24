extends SceneTree

func _initialize() -> void:
	run.call_deferred()

func capture(folder: String,label: String) -> void:
	await process_frame
	await RenderingServer.frame_post_draw
	if root.get_texture().get_image().save_jpg(folder.path_join(label+".jpg"),.92)!=OK:
		push_error("Cannot save capture")
		quit(1)

func run() -> void:
	var folder:=OS.get_cmdline_user_args()[0]
	DirAccess.make_dir_recursive_absolute(folder)
	change_scene_to_file("res://scenes/main/Main.tscn")
	await scene_changed
	var settings=root.get_node("Settings")
	var options: Dictionary=settings.values.duplicate()
	options.quality=2
	options.resolution=0
	options.render_scale=4
	settings.apply(options)
	await root.get_node("SceneRouter").show_world()
	var world=current_scene.get_node("SceneHost/SpaceWorld")
	var seq=world.sequence
	seq.set_process(false)
	world.set_process(false)
	world.select_direction(Vector3(.83,.34,.43).normalized())
	world._process(0.)
	await capture(folder,"stage04-orbit")
	options.quality=0
	settings.apply(options)
	world._process(0.)
	await capture(folder,"stage04-low")
	options.quality=2
	options.render_scale=1
	settings.apply(options)
	world._process(0.)
	await capture(folder,"stage04-scale67")
	options.render_scale=4
	settings.apply(options)
	world.set_process(true)
	world.choose_target(&"mars")
	seq.advance(.99)
	await capture(folder,"stage04-warp")
	seq.skip()
	world.choose_target(&"earth")
	seq.skip()
	world.select_direction(Vector3(.83,.34,.43).normalized())
	world.picker.get_node("Body/Power").value=100
	world.fire_rail()
	seq.advance(2.9)
	await capture(folder,"stage04-charge")
	seq.advance(2.)
	seq.advance(.29)
	await capture(folder,"stage04-flight")
	seq.advance(1.)
	for i in 3: await physics_frame
	if not seq.report:
		push_error("Missing report for capture")
		quit(1)
		return
	seq.advance(1.45)
	seq.advance(.35)
	for i in 21: await physics_frame
	await capture(folder,"stage04-impact")
	for i in 95: await physics_frame
	seq.advance(1.6)
	await capture(folder,"stage04-dispersal")
	world.fracture.weather_age=3.91
	world.fracture.update_weather()
	await capture(folder,"stage04-vacuum")
	seq.skip()
	for id in [&"venus",&"mars",&"saturn"]:
		world.choose_target(id)
		seq.skip()
		world.select_direction(Vector3(.83,.34,.43).normalized())
		world.picker.get_node("Body/Power").value=50
		world.fire_rail()
		seq.advance(5.)
		seq.advance(2.)
		for i in 3: await physics_frame
		seq.advance(1.5)
		seq.advance(.8)
		for i in 44: await physics_frame
		await capture(folder,"stage04-"+String(id))
		seq.skip()
	quit(0)
