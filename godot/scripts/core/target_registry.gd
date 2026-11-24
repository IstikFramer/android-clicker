class_name TargetRegistry
extends RefCounted

const STANDARD := [&"mercury", &"venus", &"earth", &"mars", &"saturn"]
const ALL := [&"mercury", &"venus", &"earth", &"mars", &"saturn", &"sun"]
static var definitions: Dictionary[StringName,PlanetDefinition] = {}

static func definition(id: StringName) -> PlanetDefinition:
	if not definitions.has(id):
		definitions[id] = load("res://data/planets/%s.tres" % id)
	return definitions[id]

var integrity_by_id: Dictionary[StringName, float] = {}

func _init() -> void:
	for id in ALL:
		integrity_by_id[id] = 1.0

static func allows(weapon: StringName, target: StringName) -> bool:
	match weapon:
		&"railgun", &"gungnir": return target in STANDARD
		&"vera": return target in ALL
	return false

static func instantiate_body(id: StringName, backdrop := false) -> PlanetController:
	var scene: PackedScene = load("res://scenes/planets/%s.tscn" % String(id).capitalize())
	var planet: PlanetController = scene.instantiate()
	planet.is_backdrop = backdrop
	return planet
