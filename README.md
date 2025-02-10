# Pavlovian-causal-association-tasks

Scripts for conducting causal associative learning experiments on Raspberry Pi OS.

## Prerequisites

### Operating System
Raspberry Pi OS: Bullseye (32-bit legacy)

### Python Packages
```bash
pip install numpy colorist
```

## DIY Tasks

For custom task creation, refer to `/tasks/task_template.json` for the required format.

Current implemented tasks: `pse50`, `sat50`, `sdt50`, `rpse50`, `rsat50`, `rsdt50`, `shaping05` ~ `shaping50`

Example task:
![example_task.png](figures%2Fexample_task.png)


## CheckList

Example usage of the `CheckList.py` script:
```bash
python CheckList.py -lick     # check lick sensor
python CheckList.py -puff     # check puff delivery
python CheckList.py -water    # check water delivery
python CheckList.py -camera   # check camera
python CheckList.py -wheel    # check rotatory encoder
```

## Running Tasks

Example usage of the `PavlovTasks.py` script:
```bash
python PavlovTasks.py -cam -M sat50
```
- `-cam`: Enables camera recording.
- `-m` or `-M` followed by a module name (e.g., `sat50`) should match one of your task `.json` files in `/tasks`.

Ensure that the specified module file exists.

## Directory Structure

```
pavlovian-causal-association-tasks/
├── tasks
│   ├── task_template.json  
│   └── [your_task_files].json 
├── data
│   └── .xlsx / .csv 
├── tools
│   ├── Camera.py
│   ├── LickDetector.py
│   └── PositionRecorder.py
├── utils
│   ├── Logger.py
│   ├── PinManager.py
│   └── Utils.py
├── CheckList.py
├── Config.py
├── TaskManager.py
└── PavlovTasks.py

```

## License

This project is licensed under the [MIT License](LICENSE).