# Pavlovian Causal Association Tasks

A toolkit for conducting Pavlovian causal associative learning experiments on Raspberry Pi. This system supports behavioral tracking, stimulus delivery, and data collection for neuroscience research.

## Prerequisites

**Hardware Requirements:**

- Raspberry Pi 4 (recommended)
- Solenoid valves (air puff and water delivery)
- Lick detector sensor
- Rotary encoder for locomotion tracking
- Optional: Camera module, audio buzzer

**Software Requirements:**

- Raspberry Pi OS Bullseye (32-bit legacy)
- Python 3.11+

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/barthlab/Pavlovian-causal-association-tasks.git
   cd Pavlovian-causal-association-tasks
   ```

2. Install dependencies:

   ```bash
   pip install numpy colorist flask 
   ```

3. Configure hardware connections:

   Edit `Config.py` to match your GPIO pin outs.

## Usage

### Running Experiments

Execute experiments with the main script:

```bash
python PavlovTasks.py -M acc80active -cam
```

Command Options:

- `-M <task_name>`: Specify task module (matches JSON file in `/tasks/`)
- `-cam`: Enable video recording (requires additional disk space)

You'll be prompted to enter an Experiment ID for data file naming.

### Preset Tasks

| Task | Description |
|------|-------------|
| `acc80active` | Acclimation with 80% water reward (active licking required) |
| `acc80passive` | Acclimation with 80% water reward (passive delivery) |
| `sat80active` | Stimulus association task with 80% reward probability (active) |
| `sat80passive` | Stimulus association task with 80% reward probability (passive) |
| `RandPuff` | Random air puff delivery for control experiments |

### Hardware Testing

Use `CheckList.py` to verify individual hardware components:

```bash
python CheckList.py -lick     # Test lick sensor
python CheckList.py -puff     # Test air puff delivery
python CheckList.py -water    # Test water delivery
python CheckList.py -camera   # Test camera (opens web stream)
python CheckList.py -wheel    # Test rotary encoder
python CheckList.py -buzzer   # Test audio buzzer
```

## Data Collection

The system automatically records:

- Event timeline with precise timestamps
- Lick detection data with response latencies
- Locomotion data from rotary encoder
- Video recordings (optional, .h264 format)

All data is saved to the `/data/` directory with experiment ID prefixes.

### Video Processing

Convert recorded videos to standard format:

```bash
python VideoConvert.py  # Converts .h264 → .avi (compressed)
```

## Task Configuration

Tasks are defined in JSON format with hierarchical structure.

### Example Task Structure

```json
{
  "task_name": "PSE50",
  "task_rng": "halton",
  "task_content": [
    "Timeline", [
      ["Sleep", 100],
      ["Trials", {
        "total_duration": 400,
        "trial_content": [
          "Timeline",[
            ["Sleep", [12, 18]],
            ["Buzzer", 0.1],
            ["Sleep", [1.2, 1.8]],
            ["Choice", [
              [0.5, ["Timeline", [
                ["VerticalPuff", 0.5],
                ["Sleep", 1.5],
                ["Choice", [[0.5, ["Water", 0.05]], [0.5, ["NoWater", 0.05]]]]
              ]]],
              [0.5, ["Timeline", [
                ["Blank", 0.5],
                ["Sleep", 1.5],
                ["Choice", [[0.5, ["Water", 0.05]], [0.5, ["NoWater", 0.05]]]]
              ]]]
            ]]
          ]
        ]
      }],
      ["Sleep", 100]
    ]
  ]
}
```

![Example Task Structure](figures/example_task.png)

### Available Components

- Timeline: Sequential event execution
- Trials: Repetitive blocks with specified duration
- Choice: Probabilistic branching (e.g., 80% reward rate)
- Response: Conditional actions based on animal behavior
- Hardware Events: Buzzer, VerticalPuff, HorizontalPuff, Water, etc.

## Project Structure

```text
pavlovian-causal-association-tasks/
├── tasks/                  # Task definition files (JSON)
├── data/                   # Experiment data output
├── tools/                  # Hardware interface modules
│   ├── Buzzer.py           # Audio stimulus control
│   ├── Camera.py           # Video recording
│   ├── LickDetector.py     # Lick sensor interface
│   └── PositionRecorder.py # Rotary encoder interface
├── utils/                  # Utility functions
│   ├── Logger.py           # Data logging
│   ├── PinManager.py       # GPIO pin management
│   └── Utils.py            # Miscellaneous utilities
├── CheckList.py            # Hardware testing script
├── Config.py               # System configuration
├── PavlovTasks.py          # Main experiment runner
├── RealTimeTaskManager.py  # Task execution engine
└── VideoConvert.py         # Video format conversion
```

## Extending the System

### Creating Custom Tasks

1. Create a new JSON file in `/tasks/` directory
2. Follow the hierarchical structure shown above
3. Test within `python RealTimeTaskManager.py`

### Adding Hardware Components

1. Create a new module in `/tools/` directory
2. Update `Config.py` with GPIO pin assignments
3. Modify `PavlovTasks.py` to handle new commands
4. Add testing support in `CheckList.py`

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

This project is maintained by the Barth Lab. README.md is generated by LLM. 

For technical support, bug reports, or feature requests, contact [Max](mailto:maxycc@outlook.com) or create an issue on the repository.
