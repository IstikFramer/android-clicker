class_name RailBalance
extends RefCounted

static var balance: Dictionary

static func sample(power: int) -> Dictionary:
	if balance.is_empty():
		balance=JSON.parse_string(FileAccess.get_file_as_string("res://data/balance.json"))
	var keys: Array=balance.fields
	var anchors: Array=balance.power_anchors
	for i in range(1,anchors.size()):
		var a: Array=anchors[i-1]
		var b: Array=anchors[i]
		if power<=int(b[0]):
			var t:=clampf(inverse_lerp(a[0],b[0],power),0.,1.)
			var profile: Dictionary={}
			for j in keys.size(): profile[keys[j]]=lerpf(a[j+1],b[j+1],t)
			return profile
	return {}
