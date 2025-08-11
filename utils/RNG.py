import numpy as np
from scipy.stats import qmc
import hashlib
import pickle
import Config

master_rng = np.random.default_rng(Config.RANDOMSEED)
if Config.RANDOMSEED is not None:
    print(f"Warning: RANDOMSEED is set to {Config.RANDOMSEED}. Experiments are reproducible.")


def get_short_hash(data: list) -> str:
    """Generate a short SHA-256 hash from nested list data.

    Args:
        data: Nested list to hash.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    return hashlib.sha256(pickle.dumps(data)).hexdigest()


class NumberGenerator:
    """Unified random number generator supporting multiple algorithms.

    For QMC types ('sobol', 'halton'), it uses a large pre-generated cache
    to allow for asynchronous-style access from different streams, ensuring
    the final collection of samples maintains low-discrepancy properties.
    """

    def __init__(self, generator_type: str, dimension: int = 10, pregenerate_size: int = 1000):
        """Initialize the number generator.

        Args:
            generator_type: Type of generator ('default', 'sobol', or 'halton').
            dimension: Number of independent streams to create.
            pregenerate_size: Size of pre-generated cache for QMC methods.

        Raises:
            ValueError: If dimension is not a positive integer or generator_type is invalid.
        """
        if not isinstance(dimension, int) or dimension <= 0:
            raise ValueError("Dimension must be a positive integer.")

        self.generator_type = generator_type.lower()
        print(f"Random number generator type: {self.generator_type}.")
        self.dimension = dimension

        if self.generator_type in ['sobol', 'halton']:
            qmc_class = qmc.Sobol if self.generator_type == 'sobol' else qmc.Halton
            seed = master_rng.integers(np.iinfo(np.int32).max)
            self._generator = qmc_class(d=self.dimension, scramble=True, seed=seed)

            # --- Multi-point cache and independent counters for each stream ---
            self._pregenerate_size = pregenerate_size
            self._qmc_cache = self._generator.random(n=self._pregenerate_size)
            self._qmc_counters = np.zeros(self.dimension, dtype=int)

        elif self.generator_type == 'default':
            seed_sequence = np.random.SeedSequence(master_rng.integers(2**64 - 1))
            child_seeds = seed_sequence.spawn(self.dimension)
            self._generators = [np.random.default_rng(s) for s in child_seeds]

        else:
            raise ValueError(f"Invalid generator type. Choose 'default', 'sobol', or 'halton', got {generator_type}.")

    def random_from_stream(self, stream_id: int) -> float:
        """Get the next random value from a specific stream.

        Each stream is advanced independently, maintaining proper sequence
        for quasi-Monte Carlo methods.

        Args:
            stream_id: Stream identifier (0 to dimension-1).

        Returns:
            Random float value between 0.0 and 1.0.

        Raises:
            IndexError: If stream_id is outside valid range.
        """
        if not (0 <= stream_id < self.dimension):
            raise IndexError(f"stream_id must be between 0 and {self.dimension - 1}.")

        if self.generator_type == 'default':
            return self._generators[stream_id].random()

        else: # Sobol or Halton logic using the cache
            point_index = self._qmc_counters[stream_id]

            # If the stream's counter has passed the cache size, extend the cache
            if point_index >= len(self._qmc_cache):
                print(f"Warning: QMC cache limit reached. Generating {self._pregenerate_size} more points.")
                new_points = self._generator.random(n=self._pregenerate_size)
                self._qmc_cache = np.vstack([self._qmc_cache, new_points])

            value = self._qmc_cache[point_index, stream_id]
            self._qmc_counters[stream_id] += 1
            return value