use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;

/// Start an independent deterministic stream for a snapshot seed.
pub fn seeded(seed: u64) -> ChaCha8Rng {
    ChaCha8Rng::seed_from_u64(seed)
}
