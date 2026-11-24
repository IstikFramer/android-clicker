class_name WorldSnapshot
extends RefCounted

var seed: int
var starting_integrity: Dictionary[StringName, float]

func _init(world_seed: int, registry: TargetRegistry) -> void:
	seed = world_seed
	starting_integrity = registry.integrity_by_id.duplicate()
