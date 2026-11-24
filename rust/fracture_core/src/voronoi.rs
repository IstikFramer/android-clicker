use crate::geometry::{self, Face, EPS};
use crate::rng::seeded;
use glam::{DVec3, Vec3};
use rand::Rng;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeSet, HashMap};

#[derive(Serialize, Deserialize, Debug)]
pub struct Bake {
    pub version: u32,
    pub planet_id: String,
    pub seed: u64,
    pub radius: f64,
    pub source_mesh_hash: String,
    pub source_volume: f64,
    pub cells: Vec<Cell>,
}
#[derive(Serialize, Deserialize, Debug)]
pub struct Cell {
    pub id: usize,
    pub centroid: DVec3,
    pub volume: f64,
    pub layer: String,
    pub outer_area: f64,
    pub bounds: [Vec3; 2],
    pub max_radius: f32,
    pub vertices_flat: Vec<f32>,
    pub outer_indices: Vec<u32>,
    pub inner_indices: Vec<u32>,
    pub neighbor_ids: Vec<usize>,
    pub collision_points: Vec<Vec3>,
}

fn source_hash(source: &[Face]) -> String {
    let mut hash = 0xcbf29ce484222325_u64;
    for p in source.iter().flat_map(|f| &f.points) {
        for coord in p.to_array() {
            for byte in ((coord * 1e9).round() as i64).to_le_bytes() {
                hash = (hash ^ u64::from(byte)).wrapping_mul(0x100000001b3);
            }
        }
    }
    format!("fnv1a64:{hash:016x}")
}

fn make_cell(id: usize, faces: &[Face]) -> Result<Cell, String> {
    let (volume, centroid) = geometry::volume_centroid(faces);
    if volume < 1e-10 || !volume.is_finite() || !centroid.is_finite() {
        return Err(format!("degenerate cell {id}"));
    }
    let mut neighbors = BTreeSet::new();
    let mut points = Vec::<DVec3>::new();
    let mut inner = Vec::new();
    let mut outer = Vec::new();
    let mut area = 0.0;
    for face in faces {
        if let Some(j) = face.neighbor {
            neighbors.insert(j);
        }
        for [a, b, c] in geometry::triangles(face) {
            let size = (b - a).cross(c - a).length() / 2.0;
            if size < 1e-18 {
                continue;
            }
            let indices = if face.neighbor.is_some() {
                &mut inner
            } else {
                area += size;
                &mut outer
            };
            for q in [a, b, c] {
                let index = points
                    .iter()
                    .position(|p| p.distance_squared(q) < EPS * EPS)
                    .unwrap_or_else(|| {
                        points.push(q);
                        points.len() - 1
                    });
                indices.push(index as u32);
            }
        }
    }
    let local: Vec<_> = points.iter().map(|p| (*p - centroid).as_vec3()).collect();
    let mut extrema = BTreeSet::new();
    for x in -1..=1 {
        for y in -1..=1 {
            for z in -1..=1 {
                if (x, y, z) == (0, 0, 0) {
                    continue;
                }
                let d = Vec3::new(x as f32, y as f32, z as f32);
                let index = local
                    .iter()
                    .enumerate()
                    .max_by(|a, b| a.1.dot(d).total_cmp(&b.1.dot(d)))
                    .ok_or("empty hull")?
                    .0;
                extrema.insert(index);
            }
        }
    }
    let layer = if area > 0.0 {
        "crust"
    } else if centroid.length() < 0.46 {
        "core"
    } else {
        "mantle"
    };
    Ok(Cell {
        id,
        centroid,
        volume,
        layer: layer.into(),
        outer_area: area,
        bounds: [
            local
                .iter()
                .copied()
                .fold(Vec3::splat(f32::INFINITY), Vec3::min),
            local
                .iter()
                .copied()
                .fold(Vec3::splat(f32::NEG_INFINITY), Vec3::max),
        ],
        max_radius: local.iter().map(|p| p.length()).fold(0.0, f32::max),
        vertices_flat: local.iter().flat_map(|p| p.to_array()).collect(),
        outer_indices: outer,
        inner_indices: inner,
        neighbor_ids: neighbors.into_iter().collect(),
        collision_points: extrema.into_iter().map(|i| local[i]).collect(),
    })
}

pub fn bake(planet: &str, count: usize, seed: u64) -> Result<Bake, String> {
    for attempt in 0..4u64 {
        let result = bake_once(
            planet,
            count,
            seed,
            seed.wrapping_add(attempt.wrapping_mul(0x9e3779b97f4a7c15)),
        );
        match result {
            Err(message) if attempt < 3 && message.starts_with("degenerate cell") => continue,
            other => return other,
        }
    }
    Err("could not partition all sites".into())
}

fn bake_once(planet: &str, count: usize, seed: u64, site_seed: u64) -> Result<Bake, String> {
    if !(2..=500).contains(&count) {
        return Err("count must be 2..500".into());
    }
    let source = geometry::sphere();
    let mut rng = seeded(site_seed);
    let mut sites = Vec::<DVec3>::new();
    while sites.len() < count {
        let y = rng.random_range(-1.0_f64..1.0);
        let a = rng.random_range(0.0..std::f64::consts::TAU);
        let h = (1.0 - y * y).sqrt();
        let volume_r = rng.random::<f64>();
        let r = if sites.len() % 4 == 3 {
            (0.58 + 0.42 * volume_r).cbrt()
        } else {
            volume_r.cbrt()
        };
        let p = r * DVec3::new(h * a.cos(), y, h * a.sin());
        if sites.iter().any(|q| p.distance_squared(*q) < 1e-8) {
            continue;
        }
        if source.iter().all(|face| {
            let v = &face.points;
            (v[1] - v[0]).cross(v[2] - v[0]).dot(p - v[0]) <= 0.0
        }) {
            sites.push(p);
        }
    }
    let mut cells = Vec::with_capacity(count);
    for (i, &p) in sites.iter().enumerate() {
        let mut others: Vec<_> = sites
            .iter()
            .enumerate()
            .filter(|(j, _)| *j != i)
            .map(|(j, q)| (p.distance(*q), j))
            .collect();
        others.sort_by(|a, b| a.0.total_cmp(&b.0));
        let mut faces = source.clone();
        let mut radius = 2.0;
        for (distance, j) in others {
            if distance > 2.0 * radius + EPS {
                break;
            }
            let n = (sites[j] - p) / distance;
            geometry::clip(&mut faces, n, n.dot((sites[j] + p) * 0.5), j);
            radius = faces
                .iter()
                .flat_map(|f| &f.points)
                .map(|v| v.distance_squared(p))
                .fold(0.0, f64::max)
                .sqrt();
        }
        cells.push(make_cell(i, &faces)?);
    }
    let result = Bake {
        version: 1,
        planet_id: planet.into(),
        seed,
        radius: 1.0,
        source_mesh_hash: source_hash(&source),
        source_volume: geometry::volume_centroid(&source).0,
        cells,
    };
    validate(&result)?;
    Ok(result)
}

pub fn validate(b: &Bake) -> Result<(), String> {
    let source = geometry::sphere();
    let expected = geometry::volume_centroid(&source).0;
    if b.version != 1
        || b.radius != 1.0
        || b.source_mesh_hash != source_hash(&source)
        || !(2..=500).contains(&b.cells.len())
        || !b.source_volume.is_finite()
        || (b.source_volume - expected).abs() > 1e-8
    {
        return Err("invalid source or schema".into());
    }
    let sum: f64 = b.cells.iter().map(|c| c.volume).sum();
    if !sum.is_finite() || (sum / expected - 1.0).abs() > 0.01 {
        return Err("partition volume mismatch".into());
    }
    for (i, c) in b.cells.iter().enumerate() {
        if c.id != i
            || !c.centroid.is_finite()
            || c.volume <= 0.0
            || !c.max_radius.is_finite()
            || c.max_radius <= 0.
            || !c.outer_area.is_finite()
            || c.outer_area < 0.
            || c.bounds.iter().any(|v| !v.is_finite())
            || !c.bounds[0].cmple(c.bounds[1]).all()
            || c.collision_points.iter().any(|v| !v.is_finite())
            || !c.outer_indices.len().is_multiple_of(3)
            || !c.inner_indices.len().is_multiple_of(3)
            || c.collision_points.len() < 4
            || !c.vertices_flat.len().is_multiple_of(3)
            || !c.vertices_flat.iter().all(|v| v.is_finite())
            || c.neighbor_ids.iter().any(|j| {
                *j == i
                    || b.cells
                        .get(*j)
                        .is_none_or(|other| !other.neighbor_ids.contains(&i))
            })
        {
            return Err(format!("invalid cell {i}"));
        }
        let mut edges = HashMap::<(u32, u32), (u32, i32)>::new();
        let mut signed = 0.0;
        for tri in c
            .outer_indices
            .chunks_exact(3)
            .chain(c.inner_indices.chunks_exact(3))
        {
            if tri.iter().any(|v| *v as usize >= c.vertices_flat.len() / 3) {
                return Err("index out of bounds".into());
            }
            let vertex =
                |id: u32| DVec3::from(Vec3::from_slice(&c.vertices_flat[id as usize * 3..]));
            let (a, b, d) = (vertex(tri[0]), vertex(tri[1]), vertex(tri[2]));
            signed += a.dot(b.cross(d)) / 6.0;
            for (a, b) in [(tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])] {
                let e = edges.entry((a.min(b), a.max(b))).or_default();
                e.0 += 1;
                e.1 += if a < b { 1 } else { -1 };
            }
        }
        if (signed / c.volume - 1.0).abs() > 1e-4 || edges.values().any(|e| *e != (2, 0)) {
            return Err(format!("open or inverted cell {i}"));
        }
    }
    Ok(())
}
