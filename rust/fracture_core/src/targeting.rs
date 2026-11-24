//! All distances supplied to the intersection are in target-local scene units.
use glam::{Vec2, Vec3};
use std::f32::consts::{PI, TAU};

pub fn globe_uv(direction: Vec3) -> Option<Vec2> {
    let n = direction.try_normalize()?;
    Some(Vec2::new(
        (n.z.atan2(n.x) / TAU + 0.5).rem_euclid(1.0),
        0.5 - n.y.clamp(-1.0, 1.0).asin() / PI,
    ))
}

pub fn globe_direction(uv: Vec2) -> Option<Vec3> {
    if !uv.is_finite() || !(0.0..=1.0).contains(&uv.y) {
        return None;
    }
    let lon = (uv.x.rem_euclid(1.0) - 0.5) * TAU;
    let lat = (0.5 - uv.y) * PI;
    Some(Vec3::new(
        lat.cos() * lon.cos(),
        lat.sin(),
        lat.cos() * lon.sin(),
    ))
}

pub fn pick_direction(origin: Vec3, ray: Vec3, radius: f32) -> Option<Vec3> {
    if !origin.is_finite() || !radius.is_finite() || radius <= 0.0 {
        return None;
    }
    let axis = ray.try_normalize()?;
    let along = -axis.dot(origin);
    let discriminant = radius * radius - origin.cross(axis).length_squared();
    if discriminant < 0.0 {
        return None;
    }
    let span = discriminant.sqrt();
    let t = [along - span, along + span]
        .into_iter()
        .find(|t| *t > 0.0)?;
    (origin + axis * t).try_normalize()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn spherical_orientation_and_wrap() {
        for uv in [
            Vec2::new(0.0, 0.5),
            Vec2::new(0.75, 0.5),
            Vec2::new(0.24, 0.89),
        ] {
            let actual = globe_uv(globe_direction(uv).unwrap()).unwrap();
            let du = (actual.x - uv.x + 0.5).rem_euclid(1.0) - 0.5;
            assert!(du.abs() < 1e-5 && (actual.y - uv.y).abs() < 1e-5);
        }
        assert_eq!(globe_uv(Vec3::X), Some(Vec2::splat(0.5)));
        assert_eq!(globe_uv(Vec3::Y).unwrap().y, 0.0);
        assert_eq!(globe_uv(-Vec3::Y).unwrap().y, 1.0);
        assert!(globe_uv(Vec3::ZERO).is_none());
    }

    #[test]
    fn nearest_positive_surface_or_miss() {
        assert_eq!(
            pick_direction(Vec3::X * 25.0, -Vec3::X, 10.0),
            Some(Vec3::X)
        );
        assert_eq!(pick_direction(Vec3::ZERO, Vec3::Y, 10.0), Some(Vec3::Y));
        assert!(pick_direction(Vec3::X * 25.0, Vec3::Y, 10.0).is_none());
        assert!(pick_direction(Vec3::X * 25.0, Vec3::X, 10.0).is_none());
    }
}
