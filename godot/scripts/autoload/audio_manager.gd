extends Node

var clips: Dictionary[StringName,AudioStreamWAV]={}

func play_at(player: AudioStreamPlayer3D, cue: StringName) -> void:
	if not clips.has(cue): clips[cue]=synthesize(cue)
	player.stream=clips[cue]
	player.pitch_scale=1.
	player.volume_db=-7. if cue!=&"charge" else -16.
	player.play()

func synthesize(cue: StringName) -> AudioStreamWAV:
	var rate:=22050
	var length:=1. if cue==&"charge" else (.38 if cue==&"pulse" else 1.12)
	var count:=roundi(rate*length)
	var samples:=PackedByteArray()
	samples.resize(count*2)
	var noise:=RandomNumberGenerator.new()
	noise.seed=104
	for i in count:
		var t:=float(i)/rate
		var amp: float
		match cue:
			&"charge": amp=(sin(TAU*t*88.)*.38+sin(TAU*t*176.)*.16)*(1.+.21*sin(TAU*t*6.))
			&"pulse": amp=(sin(TAU*(t*122.+12.*(1.-exp(-24.*t))))*.58+noise.randf_range(-.32,.32))*exp(-13.*t)
			_: amp=(sin(TAU*(t*43.+2.*(1.-exp(-4.*t))))*.71+sin(TAU*63.*t)*.14)*exp(-3.8*t)*smoothstep(0.,.016,t)
		samples.encode_s16(i*2,roundi(clampf(amp,-1.,1.)*26000.))
	var stream:=AudioStreamWAV.new()
	stream.format=AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate=rate
	stream.data=samples
	if cue==&"charge":
		stream.loop_mode=AudioStreamWAV.LOOP_FORWARD
		stream.loop_end=count
	return stream

func _unhandled_key_input(event: InputEvent) -> void:
	if event.is_action_pressed("mute"):
		var master := AudioServer.get_bus_index("Master")
		AudioServer.set_bus_mute(master, not AudioServer.is_bus_mute(master))
		get_viewport().set_input_as_handled()
