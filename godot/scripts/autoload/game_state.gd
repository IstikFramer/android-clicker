extends Node

var director := ShotDirector.new()
var registry := TargetRegistry.new()
var snapshot := WorldSnapshot.new(71023, registry)

func reset_world() -> void:
	director.reset()
	registry.integrity_by_id = snapshot.starting_integrity.duplicate()
	EventBus.world_reset.emit(director.generation)
