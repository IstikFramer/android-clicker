class_name FractureData
extends RefCounted

var rows: Array[Dictionary] = []
var cells: Array[Dictionary] = []
var exterior: ShaderMaterial
var interior: ShaderMaterial
var radius: float

static func vector(a: Array) -> Vector3:
	return Vector3(a[0], a[1], a[2])

func prepare(planet: PlanetController) -> bool:
	var definition := planet.definition
	radius = definition.visual_radius
	exterior = planet.surface.duplicate()
	exterior.set_shader_parameter("fragment_coords", true)
	interior = planet.material(preload("res://shaders/fracture_interior.gdshader"), {})
	if definition.type != "rocky":
		return true
	var path := "res://data/fractures/%s.json" % definition.id
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not data is Dictionary or data.get("version") != 1.0 or data.get("planet_id") != String(definition.id) or data.cells.size() != definition.fracture_count:
		push_error("Invalid baked partition: "+path)
		return false
	for raw: Dictionary in data.cells:
		var center := vector(raw.centroid)
		var points := PackedVector3Array()
		var flat: Array = raw.vertices_flat
		for i in range(0,flat.size(),3):
			points.append(Vector3(flat[i],flat[i+1],flat[i+2]))
		var hull := ConvexPolygonShape3D.new()
		var supports := PackedVector3Array()
		for xyz: Array in raw.collision_points:
			supports.append(vector(xyz)*radius*.982)
		hull.points = supports
		var mesh := ArrayMesh.new()
		var outer_index := surface_from(mesh, raw.outer_indices, points, center, true)
		var inner_index := surface_from(mesh, raw.inner_indices, points, center, false)
		rows.append({"id":int(raw.id),"centroid":center,"volume":float(raw.volume),"outer_area":float(raw.outer_area),
			"neighbor_ids":PackedInt32Array(raw.neighbor_ids),"active":false})
		cells.append({"mesh":mesh,"shape":hull,"center":center*radius,"size":float(raw.max_radius)*radius,
			"outer":outer_index,"inner":inner_index})
	return true

func surface_from(mesh: ArrayMesh, indices: Array, points: PackedVector3Array, center: Vector3, outer: bool) -> int:
	if indices.is_empty():
		return -1
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var colors := PackedColorArray()
	var uvs := PackedVector2Array()
	for t in range(0,indices.size(),3):
		var a := points[int(indices[t])]
		var b := points[int(indices[t+1])]
		var c := points[int(indices[t+2])]
		var face := (b-a).cross(c-a).normalized()
		var triangle := PackedVector3Array([a,c,b])
		var coords := PackedVector2Array()
		for v in triangle:
			var original := center+v
			var n := original.normalized()
			vertices.append(v*radius)
			normals.append(n if outer else face)
			colors.append(Color(original.x*.5+.5,original.y*.5+.5,original.z*.5+.5,1))
			coords.append(Vector2(fposmod(atan2(n.z,n.x)/TAU+.5,1),.5-asin(clampf(n.y,-1,1))/PI))
		var seam := maxf(coords[0].x,maxf(coords[1].x,coords[2].x))-minf(coords[0].x,minf(coords[1].x,coords[2].x))>.5
		for uv in coords:
			if seam and uv.x < .5: uv.x+=1.0
			uvs.append(uv)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=vertices
	arrays[Mesh.ARRAY_NORMAL]=normals
	arrays[Mesh.ARRAY_COLOR]=colors
	arrays[Mesh.ARRAY_TEX_UV]=uvs
	var index := mesh.get_surface_count()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(index,exterior if outer else interior)
	return index

func remaining() -> ArrayMesh:
	var merged := ArrayMesh.new()
	for side in ["outer","inner"]:
		var batch := SurfaceTool.new()
		var any := false
		for row in rows:
			if row.active: continue
			var cell: Dictionary = cells[row.id]
			var index: int = cell[side]
			if index < 0: continue
			if side == "inner":
				var exposed := false
				for j in row.neighbor_ids:
					if rows[j].active:
						exposed = true
						break
				if not exposed: continue
			batch.append_from(cell.mesh,index,Transform3D(Basis.IDENTITY,cell.center))
			any = true
		if any:
			batch.set_material(exterior if side == "outer" else interior)
			batch.commit(merged)
	return merged
