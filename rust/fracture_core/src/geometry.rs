//! Outward, counter-clockwise convex faces in double precision.
use glam::DVec3;
use std::f64::consts::{PI, TAU};

pub const EPS: f64 = 1e-8;
#[derive(Clone)]
pub struct Face {
    pub points: Vec<DVec3>,
    pub neighbor: Option<usize>,
}

fn outer(mut points: Vec<DVec3>) -> Face {
    if (points[1] - points[0])
        .cross(points[2] - points[0])
        .dot(points[0])
        < 0.0
    {
        points.reverse();
    }
    Face {
        points,
        neighbor: None,
    }
}

pub fn sphere() -> Vec<Face> {
    const S: usize = 48;
    const L: usize = 24;
    let mut vertices = vec![DVec3::Y];
    for i in 1..L {
        let a = PI * i as f64 / L as f64;
        for j in 0..S {
            let b = TAU * j as f64 / S as f64;
            vertices.push(DVec3::new(a.sin() * b.cos(), a.cos(), a.sin() * b.sin()));
        }
    }
    vertices.push(-DVec3::Y);
    let index = |i, j| match i {
        0 => 0,
        L => vertices.len() - 1,
        _ => 1 + (i - 1) * S + j % S,
    };
    let mut faces = Vec::new();
    for i in 0..L {
        for j in 0..S {
            let a = vertices[index(i, j)];
            let b = vertices[index(i, j + 1)];
            let c = vertices[index(i + 1, j + 1)];
            let d = vertices[index(i + 1, j)];
            if i != 0 {
                faces.push(outer(vec![a, b, c]));
            }
            if i + 1 != L {
                faces.push(outer(vec![a, c, d]));
            }
        }
    }
    faces
}

pub fn triangles(face: &Face) -> Vec<[DVec3; 3]> {
    let pts = &face.points;
    if pts.len() == 3 {
        return vec![[pts[0], pts[1], pts[2]]];
    }
    // A face center preserves collinear boundary vertices shared by adjacent faces.
    let center = pts.iter().sum::<DVec3>() / pts.len() as f64;
    (0..pts.len())
        .map(|i| [center, pts[i], pts[(i + 1) % pts.len()]])
        .collect()
}

pub fn volume_centroid(faces: &[Face]) -> (f64, DVec3) {
    let mut sum = 0.0;
    let mut centroid = DVec3::ZERO;
    for [a, b, c] in faces.iter().flat_map(triangles) {
        let v = a.dot(b.cross(c)) / 6.0;
        sum += v;
        centroid += (a + b + c) * (v / 4.0);
    }
    (sum, centroid / sum)
}

fn push_unique(points: &mut Vec<DVec3>, point: DVec3) {
    if !points.iter().any(|p| p.distance_squared(point) < EPS * EPS) {
        points.push(point);
    }
}

pub fn clip(faces: &mut Vec<Face>, n: DVec3, offset: f64, neighbor: usize) {
    if !faces
        .iter()
        .flat_map(|f| &f.points)
        .any(|p| n.dot(*p) > offset + EPS)
    {
        return;
    }
    let distance = |p| {
        let d = n.dot(p) - offset;
        if d.abs() < EPS {
            0.0
        } else {
            d
        }
    };
    let mut cap = Vec::new();
    faces.retain_mut(|face| {
        let mut out = Vec::new();
        let mut prev = *face.points.last().expect("nonempty convex face");
        let mut a = distance(prev);
        for &p in &face.points {
            let b = distance(p);
            if (a < 0.0 && b > 0.0) || (a > 0.0 && b < 0.0) {
                let q = prev.lerp(p, a / (a - b));
                push_unique(&mut out, q);
                push_unique(&mut cap, q);
            }
            if b <= 0.0 {
                push_unique(&mut out, p);
                if b == 0.0 {
                    push_unique(&mut cap, p);
                }
            }
            prev = p;
            a = b;
        }
        face.points = out;
        face.points.len() >= 3
    });
    if cap.len() >= 3 {
        let center = cap.iter().sum::<DVec3>() / cap.len() as f64;
        let u = n.any_orthonormal_vector();
        let v = n.cross(u);
        cap.sort_by(|a, b| {
            let angle = |p: DVec3| (p - center).dot(v).atan2((p - center).dot(u));
            angle(*a).total_cmp(&angle(*b))
        });
        faces.push(Face {
            points: cap,
            neighbor: Some(neighbor),
        });
    }
}
