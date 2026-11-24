extends PanelContainer

signal weapon_picked(id: StringName)
signal target_picked(id: StringName)
signal country_requested
signal station_requested
const WEAPONS := [&"railgun",&"gungnir",&"vera"]
var buttons: Dictionary[StringName,Button] = {}

func _ready() -> void:
	for w in WEAPONS:
		$Body/Weapon.add_item(String(w).to_upper())
	$Body/Weapon.item_selected.connect(func(i: int): weapon_picked.emit(WEAPONS[i]))
	for id: StringName in TargetRegistry.ALL:
		var button := Button.new()
		button.text = TargetRegistry.definition(id).name_key
		button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		button.toggle_mode = true
		button.pressed.connect(func(): target_picked.emit(id))
		$Body/Available.add_child(button)
		buttons[id] = button
	$Body/Region.pressed.connect(func(): country_requested.emit())
	$Body/Launch.pressed.connect(func(): station_requested.emit())

func refresh(weapon: StringName, d: PlanetDefinition, station: bool, population: int=-1) -> void:
	$Body/Weapon.select(WEAPONS.find(weapon))
	for id in buttons:
		buttons[id].visible = TargetRegistry.allows(weapon,id)
		buttons[id].set_pressed_no_signal(id == d.id)
		buttons[id].theme_type_variation = &"PrimaryButton" if id == d.id else &"Button"
	$Body/Name.text = d.name_key
	var lines := PackedStringArray([tr(d.type.to_upper())+"  ·  "+tr(d.atmosphere),
		tr("REF_RADIUS") % spaced(roundi(d.reference_radius_km)),tr("GAME_DISTANCE") % spaced(d.distance_game_km),
		tr("GAME_POP") % spaced(population if population>=0 else d.population)])
	if d.probes: lines.append(tr("PROBE_COUNT") % d.probes)
	$Body/Facts.text = "\n".join(lines)
	$Body/Region.visible = d.id == &"earth" and not station
	$Body/Launch.text = "TO_PLANET" if station else "TO_STATION"

static func spaced(number: int) -> String:
	var text := str(number)
	var index := text.length()-3
	while index > 0:
		text = text.insert(index," ")
		index -= 3
	return text

func controls(rail_mode: bool, busy: bool, integrity: float) -> void:
	$Body/PowerRow.visible=rail_mode
	$Body/Power.visible=rail_mode
	$Body/Power.editable=not busy
	$Body/Integrity.visible=rail_mode
	$Body/Integrity.text=tr("INTEGRITY_READ")%roundi(integrity*100.)
	$Body/Restore.visible=rail_mode and integrity<1.
	$Body/Weapon.disabled=busy
	for button in buttons.values(): button.disabled=busy
	for button in [$Body/Region,$Body/Launch]: button.disabled=busy
