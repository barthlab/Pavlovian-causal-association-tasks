import numpy as np
from scipy.stats import qmc
import hashlib
import pickle
from scipy.special import i0
# import Config
class Config:
    RANDOMSEED = 42
from collections import deque

master_rng = np.random.default_rng(Config.RANDOMSEED)
if Config.RANDOMSEED is not None:
    print(f"Warning: RANDOMSEED is set to {Config.RANDOMSEED}. Experiments are reproducible and deterministic.")


def get_short_hash(data: list) -> str:
    """Generate a short SHA-256 hash from nested list data.

    Args:
        data: Nested list to hash.

    Returns:
        Hexadecimal SHA-256 hash string.
    """
    return hashlib.sha256(pickle.dumps(data)).hexdigest()


# --- The Repulsive RNG Class ---
class RepulsivePRNG:
    """
    A pseudo-random number generator that avoids recently generated values.

    This generator maintains a history of its recent outputs and uses them
    to create a "repulsive" probability landscape, making it less likely
    to draw numbers that are close to recent ones. The generation uses
    rejection sampling with an exponential suppression model.
    """
    def __init__(self, history_size: int, concentration: float, decay: float, rng_instance: np.random.Generator):
        """
        Initializes the history-aware pseudo-random number generator.

        Args:
            history_size (int): The number of recent values to keep in memory (N).
            concentration (float): The sharpness of repulsion (kappa, κ). High values
                                   mean sharp, narrow repulsion. Low values mean broad.
            decay (float): The memory falloff (gamma, γ). 0=no memory, 1=full memory.
            rng_instance (np.random.Generator): A seeded numpy random generator for all
                                                internal random operations.
        """
        self.history = deque(maxlen=history_size)
        self.kappa = concentration
        self.gamma = decay
        self._rng = rng_instance

        # Pre-calculate the maximum potential for the subtractive method.
        # This is the peak of the von Mises PDF, which serves as our envelope M.
        if self.kappa > 0:
            self._max_potential = np.exp(self.kappa) / i0(self.kappa)
        else:
            # For a uniform distribution, the potential is always 1.
            self._max_potential = 1.0

    def _von_mises_pdf(self, x: float, mu: float) -> float:
        """Calculates the normalized PDF of the von Mises distribution for a domain of [0, 1]."""
        # i0(kappa) is the normalization constant.
        # We check for kappa > 0 to avoid division by zero if i0(0) is 0, though i0(0)=1.
        if self.kappa <= 0:
            return 1.0  # A uniform distribution
        
        numerator = np.exp(self.kappa * np.cos(2 * np.pi * (x - mu)))
        denominator = i0(self.kappa)
        return numerator / denominator

    def _repulsive_potential(self, x: float) -> float:
        """Calculates the total repulsive potential R(x) at a point x."""
        if not self.history:
            return 0.0

        potential, total_weight = 0.0, 0.0
        # The weights for history points decay exponentially. 
        for i, h in enumerate(self.history):
            weight = self.gamma ** i
            potential += weight * self._von_mises_pdf(x, h)
            total_weight += weight
        return  potential / total_weight

    def random(self) -> float:
        """Generates a new random number between 0 and 1."""
        # If history is empty, behave as a standard PRNG.
        if not self.history:
            new_val = self._rng.random()
            if self.history.maxlen > 0:
                self.history.appendleft(new_val)
            return new_val

        while True:
            candidate = self._rng.random()
            
            # Calculate the repulsive potential from the history at the candidate location.
            repulsion = self._repulsive_potential(candidate)

            # --- SUBTRACTIVE METHOD ---
            # We use rejection sampling where the acceptance probability is proportional
            # to (max_potential - current_potential
            acceptance_prob = (self._max_potential - repulsion) / self._max_potential
            if self._rng.random() < acceptance_prob:
                # Accept the candidate
                self.history.appendleft(candidate)
                return candidate


class NumberGenerator:
    """Unified random number generator supporting standard and repulsive algorithms."""

    def __init__(self, generator_type: str, dimension: int = 10, **kwargs):
        """Initialize the number generator.

        Args:
            generator_type: Type of generator ('default' or 'repulsive').
            dimension: Number of independent streams to create.
            **kwargs: Additional arguments for the 'repulsive' generator, e.g.,
                      history_size=10, concentration=5.0, decay=0.75, strength=0.9

        Raises:
            ValueError: If dimension is not a positive integer or generator_type is invalid.
        """
        if not isinstance(dimension, int) or dimension <= 0:
            raise ValueError("Dimension must be a positive integer.")

        self.generator_type = generator_type.lower()
        print(f"Random number generator type: {self.generator_type}.")
        self.dimension = dimension

        # Spawn independent child seeds from the master RNG for reproducibility
        seed_sequence = np.random.SeedSequence(master_rng.integers(2**31 - 1))
        child_seeds = seed_sequence.spawn(self.dimension)
        self._child_rngs = [np.random.default_rng(s) for s in child_seeds]

        if self.generator_type == 'default':
            # For 'default', the generators are just the child RNGs themselves
            self._generators = self._child_rngs
        elif self.generator_type == 'repulsive':
            # For 'repulsive', create a Repulsive RNG instance for each stream,
            # giving each one its own independent child RNG.
            self._generators = [
                RepulsivePRNG(
                    history_size=kwargs.get('history_size', 15),
                    concentration=kwargs.get('concentration', 0.5),
                    decay=kwargs.get('decay', 0.5),
                    rng_instance=rng
                ) for rng in self._child_rngs
            ]
        else:
            raise ValueError(f"Invalid generator type. Choose 'default' or 'repulsive', got {generator_type}.")

    def random_from_stream(self, stream_id: int) -> float:
        """Get the next random value from a specific stream.

        Args:
            stream_id: Stream identifier (0 to dimension-1).

        Returns:
            Random float value between 0.0 and 1.0.

        Raises:
            IndexError: If stream_id is outside valid range.
        """
        if not (0 <= stream_id < self.dimension):
            raise IndexError(f"stream_id must be between 0 and {self.dimension - 1}.")

        return self._generators[stream_id].random()
    

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    from collections import Counter
    import itertools

    def analyze_runs(sequence: list) -> Counter:
        if not sequence:
            return Counter()
        run_lengths = [len(list(g)) for _, g in itertools.groupby(sequence)]
        return Counter(run_lengths)
    
    # --- Tunable Parameters ---
    N_SAMPLES = 50        # Number of samples per measurement
    STREAM_ID = 0          # Which random stream to use for all tests
    N_MEASURE = 500        # Number of independent measurements for each parameter set

    # --- 1. Define the Grid Search Parameters ---
    history_sizes = [5, 10, 15]
    concentration_values = np.logspace(np.log10(0.01), np.log10(2.0), 20)
    decay_values = np.linspace(0.01, 0.99, 20)

    # Store results for both metrics
    results_mean = {hs: np.zeros((len(concentration_values), len(decay_values))) for hs in history_sizes}
    results_std = {hs: np.zeros((len(concentration_values), len(decay_values))) for hs in history_sizes}
    drift_results_mean = {hs: np.zeros((len(concentration_values), len(decay_values))) for hs in history_sizes}
    drift_results_std = {hs: np.zeros((len(concentration_values), len(decay_values))) for hs in history_sizes}

    # --- 2. Run the Baseline 'Default' Generator multiple times ---
    print(f"Running {N_MEASURE} baseline measurements...")
    baseline_run_measurements = []
    baseline_drift_measurements = []
    for _ in range(N_MEASURE):
        default_gen = NumberGenerator(generator_type='default')
        default_values = [default_gen.random_from_stream(STREAM_ID) for _ in range(N_SAMPLES)]
        default_flips = ['P' if v > 0.5 else 'b' for v in default_values]
        
        # Metric 1: Run Length
        default_run_dist = analyze_runs(default_flips)
        baseline_run_measurements.append(N_SAMPLES / sum(default_run_dist.values()))

        # Metric 2: Total Drift
        num_heads = default_flips.count('P')
        num_tails = default_flips.count('b')
        drift = abs(num_heads - num_tails)
        baseline_drift_measurements.append(drift)

    baseline_avg_run_length = np.mean(baseline_run_measurements)
    baseline_std_run_length = np.std(baseline_run_measurements)
    print(f"Baseline (Default RNG) Average Run Length: {baseline_avg_run_length:.3f} ± {baseline_std_run_length:.3f}")
    
    baseline_avg_drift = np.mean(baseline_drift_measurements)
    baseline_std_drift = np.std(baseline_drift_measurements)
    print(f"Baseline (Default RNG) Average Drift |H-T|: {baseline_avg_drift:.3f} ± {baseline_std_drift:.3f}")

    # --- 3. Perform the Grid Search with multiple measurements ---
    for hs in history_sizes:
        print(f"\nProcessing History Size: {hs}...")
        for i, conc in enumerate(concentration_values):
            for j, dec in enumerate(decay_values):
                run_measurements = []
                drift_measurements = []
                for k in range(N_MEASURE):
                    params = {'history_size': hs, 'concentration': conc, 'decay': dec}
                    gen = NumberGenerator(generator_type='repulsive', dimension=1, **params)

                    values = [gen.random_from_stream(STREAM_ID) for _ in range(N_SAMPLES)]
                    coin_flips = ['P'if v > 0.5 else'b'for v in values]
                    
                    # --- Metric 1: Average Run Length ---
                    run_distribution = analyze_runs(coin_flips)
                    total_runs = sum(run_distribution.values())
                    avg_run_length = N_SAMPLES / total_runs if total_runs > 0 else 0
                    run_measurements.append(avg_run_length)

                    # --- Metric 2: Total Drift ---
                    num_heads = coin_flips.count('P')
                    num_tails = coin_flips.count('b')
                    drift = abs(num_heads - num_tails)
                    drift_measurements.append(drift)

                # Store results for run length
                results_mean[hs][i, j] = np.mean(run_measurements)
                results_std[hs][i, j] = np.std(run_measurements)

                # Store results for drift
                drift_results_mean[hs][i, j] = np.mean(drift_measurements)
                drift_results_std[hs][i, j] = np.std(drift_measurements)

    # --- 4. Visualize the Run Length Results ---
    print("\nGenerating run length visualizations...")
    for hs in history_sizes:
        fig, ax = plt.subplots(figsize=(12, 10))

        data_mean = results_mean[hs]
        data_std = results_std[hs]

        X, Y = np.meshgrid(concentration_values, decay_values)
        im = ax.pcolormesh(X, Y, data_mean.T, cmap='viridis', shading='auto')
        ax.set_xscale('log')

        cbar = fig.colorbar(im, ax=ax, pad=0.05, shrink=0.9)
        cbar.set_label('Average Run Length (Mean)', fontsize=12, labelpad=15)

        vmin, vmax = im.get_clim()
        norm_baseline = (baseline_avg_run_length - vmin) / (vmax - vmin)
        if 0 <= norm_baseline <= 1:
            cbar.ax.plot([0, 1], [norm_baseline, norm_baseline], color='red', linestyle='--', linewidth=3)
            cbar.ax.text(1.1, norm_baseline, '<-Baseline', color='red', ha='left', va='center', fontsize=10, transform=cbar.ax.transAxes)

        for i in range(len(concentration_values)):
            for j in range(len(decay_values)):
                mean_val = data_mean[i, j]
                std_val = data_std[i, j]
                text_content = f"{mean_val:.2f}\n±{std_val:.2f}"
                bg_color_val_norm = (mean_val - vmin) / (vmax - vmin)
                text_color = "white" if bg_color_val_norm < 0.5 else "black"
                ax.text(concentration_values[i], decay_values[j], text_content, ha="center", va="center", color=text_color, fontsize=8)

        ax.set_xlabel('Concentration (κ) - Log Scale', fontsize=12)
        ax.set_ylabel('Decay (γ)', fontsize=12)
        ax.set_title(f'Average Coin Flip Run Length (History Size = {hs}, N={N_MEASURE})', fontsize=14, pad=20)
        ax.set_xticks(concentration_values)
        ax.set_xticklabels([f'{v:.1f}' for v in concentration_values], rotation=45)
        ax.set_yticks(decay_values)
        ax.set_yticklabels([f'{v:.2f}' for v in decay_values])
        
        plt.tight_layout()
        plt.savefig(f'grid_search_annotated_log_history_size_{hs}.png')
        plt.close(fig)

    print("Run length visualization complete. Check for 'grid_search_annotated_log_history_size_*.png' files.")

    # --- 5. Visualize the Drift Results ---
    print("\nGenerating drift visualizations...")

    global_vmin = baseline_avg_drift
    global_vmax = baseline_avg_drift
    for hs in history_sizes:
        min_val = np.min(drift_results_mean[hs])
        max_val = np.max(drift_results_mean[hs])
        if min_val < global_vmin:
            global_vmin = min_val
        if max_val > global_vmax:
            global_vmax = max_val

    for hs in history_sizes:
        fig, ax = plt.subplots(figsize=(12, 10))

        data_mean = drift_results_mean[hs]
        data_std = drift_results_std[hs]

        X, Y = np.meshgrid(concentration_values, decay_values)
        
        # Use the pre-calculated global vmin/vmax to ensure consistent color scales
        im = ax.pcolormesh(X, Y, data_mean.T, cmap='cividis', shading='auto', vmin=global_vmin, vmax=global_vmax)
        ax.set_xscale('log')

        cbar = fig.colorbar(im, ax=ax, pad=0.05, shrink=0.9)
        cbar.set_label('Average Total Drift |Heads-Tails| (Mean)', fontsize=12, labelpad=15)

        # Now that vmin/vmax are fixed, the baseline will always be in range.
        norm_baseline = (baseline_avg_drift - global_vmin) / (global_vmax - global_vmin)
        cbar.ax.plot([0, 1], [norm_baseline, norm_baseline], color='red', linestyle='--', linewidth=3)
        cbar.ax.text(1.1, norm_baseline, '<-Baseline', color='red', ha='left', va='center', fontsize=10, transform=cbar.ax.transAxes)

        # Add text annotations for mean ± std deviation to each cell
        for i in range(len(concentration_values)):
            for j in range(len(decay_values)):
                mean_val = data_mean[i, j]
                std_val = data_std[i, j]
                text_content = f"{mean_val:.1f}\n±{std_val:.1f}"

                bg_color_val_norm = (mean_val - global_vmin) / (global_vmax - global_vmin)
                text_color = "white" if bg_color_val_norm < 0.5 else "black"
                ax.text(concentration_values[i], decay_values[j], text_content, ha="center", va="center", color=text_color, fontsize=8)

        ax.set_xlabel('Concentration (κ) - Log Scale', fontsize=12)
        ax.set_ylabel('Decay (γ)', fontsize=12)
        ax.set_title(f'Average Total Drift |Heads-Tails| (History Size = {hs}, N={N_MEASURE})', fontsize=14, pad=20)
        ax.set_xticks(concentration_values)
        ax.set_xticklabels([f'{v:.1f}' for v in concentration_values], rotation=45)
        ax.set_yticks(decay_values)
        ax.set_yticklabels([f'{v:.2f}' for v in decay_values])

        plt.tight_layout()
        plt.savefig(f'grid_search_drift_log_history_size_{hs}.png')
        plt.close(fig)

    print("Drift visualization complete. Check for 'grid_search_drift_log_history_size_*.png' files.")