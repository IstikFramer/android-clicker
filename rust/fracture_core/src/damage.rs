//! Authored game scales, in local units and game mass.
use crate::rng::seeded;
use glam::Vec3;
use rand::Rng;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Fragment {
    pub id: usize,
    pub centroid: Vec3,
    pub volume: f64,
    #[serde(default)]
    pub outer_area: Option<f64>,
    pub neighbor_ids: Vec<usize>,
    pub active: bool,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Params {
    pub weapon_id: String,
    pub target_type: String,
    pub power: i32,
    pub local_hit_dir: Vec3,
    pub resistance: f64,
    pub seed: i64,
    pub prior_integrity: f64,
    pub scene_radius: f32,
    pub atmosphere_fraction: f64,
    pub remaining_population: i64,
}
#[derive(Debug, Serialize)]
pub struct Plan {
    pub selected_ids: Vec<usize>,
    pub impulses: Vec<Vec3>,
    pub angular_impulses: Vec<Vec3>,
    pub masses: Vec<f32>,
    pub damage_fraction: f64,
    pub integrity: f64,
    pub atmosphere_fraction: f64,
    pub crater_radius_game_km: f64,
    pub simulated_population_loss: i64,
    pub energy_index: f64,
    pub destroyed: bool,
    pub status_key: &'static str,
    pub heat_seconds: f32,
    pub wave_intensity: f32,
    pub ejecta_speed: f32,
    pub emissivity: f32,
    pub breakup_seconds: f32,
    pub annihilate: bool,
}

pub fn rail_curve(power: i32) -> f64 {
    let anchors = [
        (10, 0.02),
        (20, 0.08),
        (35, 0.22),
        (50, 0.50),
        (75, 0.78),
        (99, 0.98),
        (100, 1.0),
    ];
    for pair in anchors.windows(2) {
        let ((a, x), (b, y)) = (pair[0], pair[1]);
        if power <= b {
            let t = ((power - a) as f64 / (b - a) as f64).clamp(0., 1.);
            return x + (y - x) * t * t * (3. - 2. * t);
        }
    }
    1.
}

pub fn plan_impact(fragments: &[Fragment], p: &Params) -> Result<Plan, String> {
    let solid = p.target_type == "rocky";
    let star = p.target_type == "star";
    let full = match (p.weapon_id.as_str(), p.power) {
        ("railgun", 10..=100) if !star => p.power == 100,
        ("gungnir", 100) if !star => true,
        ("vera", 20..=100) => true,
        _ => return Err("unsupported weapon, target or power".into()),
    };
    if !(solid || star || p.target_type == "gas")
        || solid == fragments.is_empty()
        || fragments.len() > 500
        || !p.local_hit_dir.is_finite()
        || !p.local_hit_dir.is_normalized()
        || !p.resistance.is_finite()
        || (!star && p.resistance <= 0.)
        || !p.scene_radius.is_finite()
        || !(0.01..=1000.).contains(&p.scene_radius)
        || !(0.0..=1.).contains(&p.atmosphere_fraction)
        || !(0.0..=1.).contains(&p.prior_integrity)
        || p.prior_integrity == 0.
        || p.remaining_population < 0
    {
        return Err("invalid impact metadata".into());
    }
    let mut cells: Vec<_> = fragments.iter().collect();
    cells.sort_by_key(|c| c.id);
    for (i, c) in cells.iter().enumerate() {
        if c.id != i
            || !c.centroid.is_finite()
            || c.centroid.length_squared() > 1.001
            || !(1e-12..=5.).contains(&c.volume)
            || c.outer_area.is_some_and(|a| !(0.0..=13.).contains(&a))
            || c.neighbor_ids
                .iter()
                .enumerate()
                .any(|(k, j)| c.neighbor_ids[..k].contains(j))
            || c.neighbor_ids.len() > cells.len()
            || c.neighbor_ids
                .iter()
                .any(|&j| j == i || j >= cells.len() || !cells[j].neighbor_ids.contains(&i))
        {
            return Err("invalid fragment or adjacency".into());
        }
    }
    let total: f64 = cells.iter().map(|c| c.volume).sum();
    let available: f64 = cells.iter().filter(|c| !c.active).map(|c| c.volume).sum();
    if solid && (available == 0. || (available / total - p.prior_integrity).abs() > 1e-4) {
        return Err("inconsistent prior integrity".into());
    }
    let gain = if full {
        1.
    } else {
        (rail_curve(p.power) / p.resistance.clamp(0.65, 1.5)).min(0.995)
    };
    let t = p.power as f32 / 100.;
    let speed = match p.weapon_id.as_str() {
        "vera" => 13. + 12. * t,
        "gungnir" => 12.,
        _ => 0.8 + 11.2 * t,
    };
    let mut rng = seeded(p.seed as u64);
    let scores: Vec<_> = cells
        .iter()
        .map(|c| {
            let radial = c.centroid.normalize_or_zero();
            let alignment = 1. - radial.dot(p.local_hit_dir);
            let depth = 1. - c.centroid.length();
            let branch = if p.power >= 50 {
                0.45 * (radial.x * 8. + radial.z * 5.).sin().abs()
            } else {
                0.
            };
            c.centroid.distance(p.local_hit_dir)
                + 0.55 * alignment
                + 0.55 * depth
                + branch
                + rng.random_range(0.0..0.035)
        })
        .collect();
    let mut ranked: Vec<_> = (0..cells.len()).filter(|&i| !cells[i].active).collect();
    ranked.sort_by(|&a, &b| scores[a].total_cmp(&scores[b]).then(a.cmp(&b)));
    let mut picked = vec![false; cells.len()];
    let mut front = vec![false; cells.len()];
    let mut ids = Vec::new();
    let mut impulses = Vec::new();
    let mut torques = Vec::new();
    let mut masses = Vec::new();
    let mut detached = 0.;
    let mut footprint = 0.;
    while solid && (full || detached < gain * available) {
        let first = ranked.iter().copied().find(|&i| !picked[i]);
        let next = if p.power < 50 && !full {
            ranked
                .iter()
                .copied()
                .find(|&i| !picked[i] && front[i])
                .or(first)
        } else {
            first
        };
        let Some(i) = next else {
            break;
        };
        let c = cells[i];
        picked[i] = true;
        for &j in &c.neighbor_ids {
            front[j] = true;
        }
        let mass = (c.volume as f32 * 75.).clamp(0.05, 5.);
        let radial = c.centroid.normalize_or_zero();
        let noise = Vec3::new(
            rng.random_range(-1.0..1.),
            rng.random_range(-1.0..1.),
            rng.random_range(-1.0..1.),
        );
        let tangent = noise - radial * noise.dot(radial);
        let away = (c.centroid - p.local_hit_dir).normalize_or_zero();
        let axis = if p.weapon_id == "gungnir" {
            radial - 0.65 * p.local_hit_dir
        } else {
            radial + 0.52 * away
        };
        let velocity = (axis + 0.18 * tangent).normalize_or_zero()
            * speed
            * (0.70 + 0.30 * (1. - c.centroid.distance(p.local_hit_dir) * 0.5));
        ids.push(i);
        masses.push(mass);
        impulses.push(velocity * mass);
        torques.push(noise * mass * (0.05 + 0.45 * t));
        detached += c.volume;
        footprint += c.outer_area.unwrap_or_else(|| {
            c.volume.powf(2. / 3.) * f64::from((c.centroid.length() - 0.64).max(0.) * 3.)
        });
    }
    let damage = if solid {
        (detached / total).min(p.prior_integrity)
    } else {
        p.prior_integrity * gain
    };
    let integrity = if full || (solid && ids.len() == ranked.len()) {
        0.
    } else {
        (p.prior_integrity - damage).max(0.)
    };
    let destroyed = integrity == 0.;
    let status_key = match (p.target_type.as_str(), destroyed) {
        ("star", _) => "solar_impact",
        ("gas", true) => "gas_dispersed",
        ("gas", false) => "gas_impact",
        (_, true) => "solid_destroyed",
        _ => "solid_impact",
    };
    let loss = if destroyed {
        p.remaining_population
    } else {
        (p.remaining_population as f64 * (damage / p.prior_integrity) * 0.75).round() as i64
    };
    let visual_gain = if p.weapon_id == "vera" {
        3.4
    } else if p.weapon_id == "gungnir" {
        1.3
    } else {
        1.
    };
    Ok(Plan {
        selected_ids: ids,
        impulses,
        angular_impulses: torques,
        masses,
        damage_fraction: damage,
        integrity,
        atmosphere_fraction: if destroyed {
            0.
        } else {
            (p.atmosphere_fraction - damage * (0.4 + 0.6 * f64::from(t))).max(0.)
        },
        crater_radius_game_km: if solid && !destroyed {
            f64::from(p.scene_radius) * 100. * (footprint / std::f64::consts::PI).sqrt()
        } else {
            0.
        },
        simulated_population_loss: loss.clamp(0, p.remaining_population),
        energy_index: f64::from(t * speed * 100.),
        destroyed,
        status_key,
        heat_seconds: (2. + 6. * t) * visual_gain,
        wave_intensity: (0.25 + t * 1.8) * visual_gain,
        emissivity: (1. + 4. * t) * visual_gain,
        ejecta_speed: speed,
        breakup_seconds: if p.weapon_id == "vera" {
            (2. - 2. * t).max(0.12)
        } else {
            0.18 + 0.65 * (1. - t)
        },
        annihilate: p.weapon_id == "vera" && p.power == 100,
    })
}
