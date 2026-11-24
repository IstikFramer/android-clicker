extends RefCounted

func check(expect: Callable) -> void:
	var sockets := {"Railgun":["Muzzle","WarpOrigin","CameraAnchor","RecoilPivot"],
		"Gungnir":["LaunchGate","ProjectileAnchor","OverviewCamera","ExitAnchor"],
		"Vera":["BeamOrigin","CameraAnchor","RingPivot","CoreAnchor","ArcSection3"]}
	for asset in ["Railgun","RailgunMedium","Gungnir","GungnirProjectile","Vera","VeraMedium",
			"MercuryStation","MarsDomes","SaturnStation","SaturnRings","Rock00","Rock01","Rock02","Rock03","Rock04","Rock05","Rock06","Rock07"]:
		var model: Node3D = load("res://assets/models/%s.glb" % asset).instantiate()
		expect.call(not model.find_children("*","MeshInstance3D",true,false).is_empty(),"mesh: "+asset)
		for id in sockets.get(asset.trim_suffix("Medium"),[]):
			expect.call(model.find_child(id,true,false) != null,"imported socket: "+id)
		model.free()
	var base: PlanetController = preload("res://scenes/planets/PlanetBase.tscn").instantiate()
	expect.call(base.definition.visual_radius == 10,"default local scale")
	base.free()
