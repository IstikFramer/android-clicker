use fracture_core::damage::{self, Fragment, Params};
use glam::Vec3;
use godot::builtin::{PackedFloat32Array, PackedInt32Array, PackedVector3Array};
use godot::prelude::*;

pub fn field<T: FromGodot>(d: &VarDictionary, key: &str) -> Result<T, String> {
    d.get(key)
        .ok_or_else(|| format!("missing {key}"))?
        .try_to()
        .map_err(|_| format!("invalid {key}"))
}
fn name(d: &VarDictionary, key: &str) -> Result<String, String> {
    field::<GString>(d, key)
        .map(|v| v.to_string())
        .or_else(|_| field::<StringName>(d, key).map(|v| v.to_string()))
}
fn vec(v: Vector3) -> Vec3 {
    Vec3::new(v.x, v.y, v.z)
}
pub fn packed(v: Vec<Vec3>) -> PackedVector3Array {
    v.into_iter().map(|p| Vector3::new(p.x, p.y, p.z)).collect()
}
pub fn plan(rows: &Array<VarDictionary>, p: &VarDictionary) -> Result<VarDictionary, String> {
    if rows.len() > 500 {
        return Err("too many cells".into());
    }
    let params = Params {
        weapon_id: name(p, "weapon_id")?,
        target_type: name(p, "target_type")?,
        power: field(p, "power")?,
        local_hit_dir: vec(field(p, "local_hit_dir")?),
        resistance: field(p, "resistance")?,
        seed: field(p, "seed")?,
        prior_integrity: field(p, "prior_integrity")?,
        scene_radius: field(p, "scene_radius")?,
        atmosphere_fraction: field(p, "atmosphere_fraction")?,
        remaining_population: field(p, "remaining_population")?,
    };
    let mut fragments = Vec::with_capacity(rows.len());
    for d in rows.iter_shared() {
        let neighbors: PackedInt32Array = field(&d, "neighbor_ids")?;
        let neighbor_ids = neighbors
            .as_slice()
            .iter()
            .map(|&v| usize::try_from(v).map_err(|_| "negative neighbor"))
            .collect::<Result<_, _>>()?;
        fragments.push(Fragment {
            id: usize::try_from(field::<i64>(&d, "id")?).map_err(|_| "negative id")?,
            centroid: vec(field(&d, "centroid")?),
            volume: field(&d, "volume")?,
            outer_area: d
                .get("outer_area")
                .map(|v| v.try_to::<f64>().map_err(|_| "invalid outer_area"))
                .transpose()?,
            active: field(&d, "active")?,
            neighbor_ids,
        });
    }
    let r = damage::plan_impact(&fragments, &params)?;
    let ids: PackedInt32Array = r.selected_ids.into_iter().map(|i| i as i32).collect();
    Ok(vdict! {
        "ok" => true,"error" => "","selected_ids" => &ids,"impulses" => &packed(r.impulses),"angular_impulses" => &packed(r.angular_impulses),
        "masses" => &PackedFloat32Array::from(r.masses.as_slice()),"damage_fraction" => r.damage_fraction,"integrity" => r.integrity,
        "atmosphere_fraction" => r.atmosphere_fraction,"crater_radius_game_km" => r.crater_radius_game_km,
        "simulated_population_loss" => r.simulated_population_loss,"energy_index" => r.energy_index,"destroyed" => r.destroyed,
        "status_key" => r.status_key,"heat_seconds" => r.heat_seconds,"wave_intensity" => r.wave_intensity,
        "ejecta_speed" => r.ejecta_speed,"emissivity" => r.emissivity,"breakup_seconds" => r.breakup_seconds,"annihilate" => r.annihilate
    })
}
