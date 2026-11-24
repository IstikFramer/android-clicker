use glam::Vec3;

pub fn accelerations(
    pos: &[Vec3],
    mass: &[f32],
    g: f32,
    softening: f32,
    limit: f32,
) -> Result<Vec<Vec3>, String> {
    if pos.len() != mass.len()
        || pos.len() > 96
        || !g.is_finite()
        || !(0.0..=10.).contains(&g)
        || !softening.is_finite()
        || !(0.01..=100.).contains(&softening)
        || !limit.is_finite()
        || !(0.0..=30.).contains(&limit)
        || pos
            .iter()
            .any(|p| !p.is_finite() || p.abs().max_element() > 1e6)
        || mass.iter().any(|m| !m.is_finite() || *m <= 0. || *m > 1e5)
    {
        return Err("invalid gravity input".into());
    }
    let mut acc = vec![Vec3::ZERO; pos.len()];
    for i in 0..pos.len() {
        for j in i + 1..pos.len() {
            let d = pos[j] - pos[i];
            let r2 = d.length_squared() + softening * softening;
            let pair = d * (g / (r2 * r2.sqrt()));
            acc[i] += mass[j] * pair;
            acc[j] -= mass[i] * pair;
        }
    }
    for a in &mut acc {
        *a = a.clamp_length_max(limit);
    }
    Ok(acc)
}
