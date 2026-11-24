use fracture_core::{damage::*, gravity::accelerations, rng::seeded, voronoi::*};
use glam::{DVec3, Vec3};
use rand::Rng;
use std::sync::OnceLock;

fn earth() -> &'static Bake {
    static EARTH: OnceLock<Bake> = OnceLock::new();
    EARTH.get_or_init(|| {
        serde_json::from_str(include_str!("../../../godot/data/fractures/earth.json")).unwrap()
    })
}

fn metadata() -> Vec<Fragment> {
    earth()
        .cells
        .iter()
        .map(|c| Fragment {
            id: c.id,
            centroid: c.centroid.as_vec3(),
            volume: c.volume,
            outer_area: Some(c.outer_area),
            neighbor_ids: c.neighbor_ids.clone(),
            active: false,
        })
        .collect()
}
fn params(power: i32) -> Params {
    Params {
        weapon_id: "railgun".into(),
        target_type: "rocky".into(),
        power,
        local_hit_dir: Vec3::X,
        resistance: 1.,
        seed: 741,
        prior_integrity: 1.,
        scene_radius: 10.,
        atmosphere_fraction: 1.,
        remaining_population: 8_000_000_000,
    }
}

#[test]
fn curve_mass_connectivity_and_profiles() {
    let cells = metadata();
    for (power, ratio) in [
        (10, 0.02),
        (20, 0.08),
        (35, 0.22),
        (50, 0.50),
        (75, 0.78),
        (99, 0.98),
        (100, 1.),
    ] {
        let p = plan_impact(&cells, &params(power)).unwrap();
        assert!((p.damage_fraction - ratio).abs() < 0.008);
        let mut region = Vec::new();
        for (k, &i) in p.selected_ids.iter().enumerate() {
            if power < 50 && k > 0 {
                assert!(cells[i].neighbor_ids.iter().any(|n| region.contains(n)));
            }
            region.push(i);
            assert!(p.impulses[k].is_finite() && p.angular_impulses[k].is_finite());
            assert!(p.impulses[k].length() / p.masses[k] < 30.);
        }
        assert!(p.simulated_population_loss <= 8_000_000_000);
    }
    let mut last = plan_impact(&cells, &params(10)).unwrap();
    for power in 11..=100 {
        assert!(rail_curve(power) > rail_curve(power - 1));
        let next = plan_impact(&cells, &params(power)).unwrap();
        assert!(
            next.heat_seconds > last.heat_seconds
                && next.emissivity > last.emissivity
                && next.wave_intensity > last.wave_intensity
                && next.ejecta_speed > last.ejecta_speed
        );
        last = next;
    }
    assert_eq!(last.simulated_population_loss, 8_000_000_000);
    let mut weak = params(35);
    weak.resistance = 0.75;
    assert!(plan_impact(&cells, &weak).unwrap().damage_fraction > rail_curve(35) + 0.01);
}

#[test]
fn repeat_and_directed_weapons() {
    let mut cells = metadata();
    let mut p = params(20);
    let one = plan_impact(&cells, &p).unwrap();
    let two = plan_impact(&cells, &p).unwrap();
    assert_eq!(one.impulses, two.impulses);
    for id in one.selected_ids {
        cells[id].active = true;
    }
    p.prior_integrity = one.integrity;
    p.atmosphere_fraction = one.atmosphere_fraction;
    p.remaining_population -= one.simulated_population_loss;
    let partial = plan_impact(&cells, &p).unwrap();
    assert!(
        partial.integrity < p.prior_integrity
            && partial.atmosphere_fraction <= p.atmosphere_fraction
    );
    for id in &partial.selected_ids {
        assert!(!cells[*id].active);
    }
    p.power = 100;
    let full = plan_impact(&cells, &p).unwrap();
    assert_eq!(full.integrity, 0.);
    assert_eq!(
        full.selected_ids.len(),
        cells.iter().filter(|c| !c.active).count()
    );
    p.weapon_id = "gungnir".into();
    let axial = plan_impact(&cells, &p).unwrap();
    assert_eq!(full.selected_ids, axial.selected_ids);
    assert_ne!(full.impulses, axial.impulses);
    p.weapon_id = "vera".into();
    for power in [20, 50, 100] {
        p.power = power;
        let v = plan_impact(&cells, &p).unwrap();
        assert!(
            v.destroyed
                && v.selected_ids.len() == full.selected_ids.len()
                && v.ejecta_speed > full.ejecta_speed
        );
        assert_eq!(v.annihilate, power == 100);
        if power == 50 {
            assert_eq!(v.breakup_seconds, 1.);
        }
    }
}

#[test]
fn fluid_and_invalid_inputs() {
    let mut p = params(20);
    p.target_type = "gas".into();
    let gas = plan_impact(&[], &p).unwrap();
    assert!(
        gas.selected_ids.is_empty()
            && gas.crater_radius_game_km == 0.
            && gas.status_key == "gas_impact"
    );
    p.target_type = "star".into();
    assert!(plan_impact(&[], &p).is_err());
    p.weapon_id = "vera".into();
    p.resistance = -1.;
    assert_eq!(plan_impact(&[], &p).unwrap().status_key, "solar_impact");
    let mut cells = metadata();
    p = params(20);
    p.local_hit_dir = Vec3::NAN;
    assert!(plan_impact(&cells, &p).is_err());
    cells[1].id = 0;
    assert!(plan_impact(&cells, &params(20)).is_err());
}

#[test]
fn gravity_momentum_and_rejection() {
    let pos = [Vec3::ZERO, Vec3::X * 2.];
    let m = [1., 3.];
    let a = accelerations(&pos, &m, 0.1, 0.3, 3.).unwrap();
    assert!(a[0].x > 0. && a[1].x < 0. && (a[0] * m[0] + a[1] * m[1]).length() < 1e-7);
    assert_eq!(
        accelerations(&[Vec3::ZERO; 2], &m, 0.1, 0.3, 3.).unwrap(),
        [Vec3::ZERO; 2]
    );
    assert!(accelerations(&pos, &[1.], 0.1, 0.3, 3.).is_err());
    assert!(accelerations(&[Vec3::NAN], &[1.], 0.1, 0.3, 3.).is_err());
    assert!(accelerations(&[Vec3::ZERO; 97], &[1.; 97], 0.1, 0.3, 3.).is_err());
}

fn point(c: &Cell, i: u32) -> DVec3 {
    c.centroid + Vec3::from_slice(&c.vertices_flat[i as usize * 3..]).as_dvec3()
}

#[test]
fn shared_boundaries_and_sample_ownership() {
    let b = earth();
    validate(b).unwrap();
    let mut rng = seeded(99);
    for c in &b.cells {
        for &j in &c.neighbor_ids {
            if j <= c.id {
                continue;
            }
            let other = &b.cells[j];
            // Adjacent convex cells must share at least three noncollinear points.
            let mut shared = Vec::new();
            for i in 0..c.vertices_flat.len() / 3 {
                let v = point(c, i as u32);
                if (0..other.vertices_flat.len() / 3)
                    .any(|k| v.distance_squared(point(other, k as u32)) < 1e-13)
                {
                    shared.push(v);
                }
            }
            assert!(shared.len() >= 3);
            // Use a broad triangle rather than normalizing roundoff along a clipped edge.
            let edge = shared
                .iter()
                .map(|v| *v - shared[0])
                .max_by(|a, b| a.length_squared().total_cmp(&b.length_squared()))
                .unwrap();
            let normal = shared
                .iter()
                .map(|v| edge.cross(*v - shared[0]))
                .max_by(|a, b| a.length_squared().total_cmp(&b.length_squared()))
                .unwrap();
            assert!(normal.length_squared() > 1e-20);
            let n = normal.normalize();
            assert!(shared.iter().all(|v| n.dot(*v - shared[0]).abs() < 1e-5));
            assert!(n.dot(c.centroid - shared[0]) * n.dot(other.centroid - shared[0]) < 0.);
        }
    }
    for _ in 0..1200 {
        let sample = DVec3::from_array(std::array::from_fn(|_| rng.random_range(-0.98..=0.98)));
        if sample.length() > 0.98 {
            continue;
        }
        let owners = b
            .cells
            .iter()
            .filter(|c| {
                let local = (sample - c.centroid).as_vec3();
                local.cmpge(c.bounds[0]).all()
                    && local.cmple(c.bounds[1]).all()
                    && c.outer_indices
                        .chunks_exact(3)
                        .chain(c.inner_indices.chunks_exact(3))
                        .all(|tri| {
                            let a = point(c, tri[0]);
                            (point(c, tri[1]) - a)
                                .cross(point(c, tri[2]) - a)
                                .dot(sample - a)
                                <= 1e-10
                        })
            })
            .count();
        assert_eq!(owners, 1);
    }
}

#[test]
fn reproducible_bake() {
    let a = bake("sample", 16, 91).unwrap();
    let b = bake("sample", 16, 91).unwrap();
    assert_eq!(
        serde_json::to_vec(&a).unwrap(),
        serde_json::to_vec(&b).unwrap()
    );
}
