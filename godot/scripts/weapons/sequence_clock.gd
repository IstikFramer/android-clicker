class_name SequenceClock
extends RefCounted

var previous_usec: int
var suspended:=false

func restart() -> void:
	previous_usec=Time.get_ticks_usec()

func step(paused: bool) -> float:
	var now:=Time.get_ticks_usec()
	var delta:=minf(.25,(now-previous_usec)*.000001) if previous_usec else 0.
	previous_usec=now
	return 0. if paused or suspended else delta
