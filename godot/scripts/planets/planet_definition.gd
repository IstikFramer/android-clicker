class_name PlanetDefinition
extends Resource

@export var id: StringName
@export var name_key: StringName
@export_enum("rocky","gas","star") var type: String = "rocky"
@export var visual_radius := 10.0
@export var reference_radius_km: float
@export var distance_game_km: int
@export var population: int
@export var probes: int
@export var atmosphere: StringName
@export var day_map: Texture2D
@export var night_map: Texture2D
@export var cloud_map: Texture2D
@export var ocean_mask: Texture2D
@export var tint: Color
@export var accent: Color
@export var rotation_rate: float
@export var fracture_count: int
@export var damage_resistance: float
@export var news_channel: StringName
