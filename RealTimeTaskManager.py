"""Real-time task manager for behavioral experiments.

This module provides the core task execution engine for Pavlovian causal
association experiments. It handles task visualization, execution timing,
and data logging while supporting complex nested task structures.
"""

import time
import os
import os.path as path
import json
import numpy as np
from copy import deepcopy
from typing import Any, List, Tuple
from utils.Logger import CSVFile
from utils.Utils import tab_block, cprint, uprint, GetTime
import Config
from utils.RNG import NumberGenerator, get_short_hash


class TaskInstance:
    """Task execution instance with visualization and logging capabilities.

    Manages the execution of behavioral tasks defined in JSON format,
    providing ASCII visualization of task structure and real-time execution
    with precise timing and data logging.
    """
    def __init__(self, module_json: dict, exp_name: str, lick_detector=None):
        """Initialize task instance with configuration and logging.

        Args:
            module_json: Task configuration dictionary loaded from JSON file.
            exp_name: Experiment name for data file naming.
            lick_detector: Optional lick detector instance for behavioral monitoring.
        """
        self.log_history = []

        self.module_json = module_json
        self.task_name = self.module_json["task_name"]

        # Random number generator
        self.rng = NumberGenerator(self.module_json.get("task_rng", "default").lower())
        self.stream_dict = {}

        # Lick detector
        self.lick_detector = lick_detector

        # Log file
        self.writer = CSVFile(
            path.join(Config.SAVE_DIR, f"TIMELINE_{exp_name}.csv"), ["time", "details"]
        )
        self.vis()

    def vis(self):
        """Generate and print ASCII art representation of the task structure.

        Creates a visual representation of the task flow including timelines,
        choices, and response windows. This method preserves the existing
        display format for user task visualization.
        """
        print(f"Task Name: {self.task_name}")

        def recursive_paint(tmp_list: Tuple[str, Any]) -> List[str]:
            """
            Recursively builds an ASCII art representation of a task component.

            This function traverses the nested task structure. For each component
            type (e.g., "Timeline", "Choice"), it generates a multi-line string
            block (a list of strings) and combines them to represent the task flow.

            Args:
                tmp_list: A [key, value] pair from the task structure, e.g.,
                          ["Timeline", [...]].

            Returns:
                A list of strings, where each string is a row of the generated
                ASCII art. All strings in the list are guaranteed to have the same length.
            """
            tmp_key, tmp_value = tmp_list
            final_blocks = []

            # --- Timeline: A horizontal sequence of events ---
            if tmp_key == "Timeline":
                # First, recursively render all sub-components to find the required
                # canvas dimensions (max height and total width).
                result_blocks = [recursive_paint(item) for item in tmp_value]
                max_height = max(len(block) for block in result_blocks)
                max_width = (
                    sum(len(block[0]) for block in result_blocks)
                    + len(result_blocks)
                    + 1
                )

                # Create a blank canvas and paste each component side-by-side,
                # centered vertically within the timeline.
                final_blocks = [" " * max_width for _ in range(max_height)]
                width_ptr = 1
                for block in result_blocks:
                    height, width = len(block), len(block[0])
                    start_height = (max_height - height) // 2
                    for i, row_content in enumerate(block):
                        row_idx = start_height + i
                        final_blocks[row_idx] = (
                            final_blocks[row_idx][:width_ptr]
                            + row_content
                            + final_blocks[row_idx][width_ptr + width :]
                        )
                    width_ptr += width + 1

            # --- Trials: A repeating container ---
            elif tmp_key == "Trials":
                # Render the inner content and wrap it in a container labeled "N x"
                # to signify a repeating trial.
                result_block = recursive_paint(tmp_value["trial_content"])
                new_strings = tab_block(
                    *result_block, f"{tmp_value['total_duration']} s", sub_char="-"
                )

                max_height = len(new_strings) + 1
                max_width = len(new_strings[0]) + 7
                center_height = max_height // 2
                final_blocks = [" " * max_width for _ in range(max_height)]

                for i, line in enumerate(new_strings):
                    final_blocks[i + 1] = f"     |{line}|"
                final_blocks[center_height] = " N x " + final_blocks[center_height][5:]

            # --- Choice: Vertical branching with probabilities ---
            elif tmp_key == "Choice":
                # Render each choice, align them to a uniform width, and stack them
                # vertically with a branching line showing the probability of each path.
                result_blocks = [recursive_paint(choice[1]) for choice in tmp_value]
                max_width = max(len(block[0]) for block in result_blocks)

                prob_strings = [f"-{int(choice[0] * 100)}%-" for choice in tmp_value]
                _, *sync_prob_strings = tab_block(*prob_strings)

                for i, (prob_str, block) in enumerate(
                    zip(sync_prob_strings, result_blocks)
                ):
                    _, *sync_strings, _ = tab_block(
                        *block, " " * max_width, centering=False
                    )
                    new_strings = [
                        " " * (len(prob_str) + 1) + single_sync_string
                        for single_sync_string in sync_strings
                    ]
                    center_height = len(new_strings) // 2
                    new_strings[center_height] = (
                        f" {prob_str}{new_strings[center_height][1 + len(prob_str) :]}"
                    )

                    # Draw vertical connector lines for the branches.
                    if i < len(tmp_value) - 1:  # Not the last choice
                        for row in range(center_height, len(new_strings)):
                            new_strings[row] = f"|{new_strings[row][1:]}"
                    if i > 0:  # Not the first choice
                        for row in range(center_height + 1):
                            new_strings[row] = f"|{new_strings[row][1:]}"
                    final_blocks.extend(new_strings)

            # --- Response: Vertical lick vs. no-lick decision ---
            elif tmp_key == "Response":
                # Similar to "Choice", but for a binary lick/no-lick decision.
                # Renders both outcomes and stacks them with a connecting branch.
                lick_blocks = recursive_paint(tmp_value["lick"])
                no_lick_blocks = recursive_paint(tmp_value["no-lick"])
                max_width = max(len(lick_blocks[0]), len(no_lick_blocks[0]))

                _, *response_strings = tab_block(
                    "-lick-",
                    f"|> lick in {tmp_value['total_duration']}s <|",
                    "-no-lick-",
                )

                for i, (resp_str, block) in enumerate(
                    zip(
                        response_strings,
                        [
                            lick_blocks,
                            [
                                " ",
                            ],
                            no_lick_blocks,
                        ],
                    )
                ):
                    _, *sync_strings, _ = tab_block(
                        *block, " " * max_width, centering=False
                    )
                    new_strings = [
                        " " * (len(resp_str) + 1) + single_sync_string
                        for single_sync_string in sync_strings
                    ]
                    center_height = len(new_strings) // 2
                    new_strings[center_height] = (
                        f" {resp_str}{new_strings[center_height][1 + len(resp_str) :]}"
                    )

                    # Draw vertical connector lines.
                    if i < 2:  # Top (lick) branch
                        for row in range(center_height, len(new_strings)):
                            new_strings[row] = f"|{new_strings[row][1:]}"
                    if i > 0:  # Bottom (no-lick) branch
                        for row in range(center_height + 1):
                            new_strings[row] = f"|{new_strings[row][1:]}"
                    final_blocks.extend(new_strings)

            # --- Base Cases: Simple timed events ---
            elif tmp_key in (
                "Sleep",
                "VerticalPuff",
                "HorizontalPuff",
                "PeltierLeft",
                "PeltierRight",
                "PeltierBoth",
                "Blank",
                "Water",
                "NoWater",
                "FakeRelay",
            ) or "Buzzer" in tmp_key:
                # These are terminal nodes. Format the event name and duration into a
                # simple, standardized block, handling both fixed and ranged durations.
                duration_str = (
                    f"{tmp_value} s"
                    if not isinstance(tmp_value, list)
                    else f"{tmp_value[0]}~{tmp_value[1]} s"
                )
                _, string_key, string_duration = tab_block(
                    f"-{tmp_key}-", f"-{duration_str}-", sub_char="-"
                )
                final_blocks = [" " * len(string_key), string_key, string_duration]
            elif tmp_key == "LED":
                color, control = tmp_value
                color = color.lower()
                if isinstance(control, list):
                    control = f"{control[0]}~{control[1]} s"
                elif isinstance(control, (int, float)):
                    control = f"{control} s"
                else:
                    control = f"{control}"
                
                _, string_key, string_duration = tab_block(
                    f"-{color}{tmp_key}-", f"-{control}-", sub_char="-"
                )
                final_blocks = [" " * len(string_key), string_key, string_duration]

            # --- Error Handling ---
            elif tmp_key in ("Pass",):
                final_blocks = [
                    " ",
                ]
            else:
                raise NotImplementedError(
                    f"JSON command '{tmp_key}' is not implemented!"
                )

            # Sanity check to ensure all lines in a block have the same width.
            assert len(set(map(len, final_blocks))) == 1, (
                f"Block for '{tmp_key}' has inconsistent line widths."
            )
            return final_blocks

        # Generate and print the final ASCII art for the entire task.
        vis_block = recursive_paint(self.module_json["task_content"])
        for vis_line in vis_block:
            uprint(vis_line)

    def run(self):
        """
        A generator that executes a behavioral task based on a configuration.

        Yields:
            str: Commands to control hardware.
        """
        cprint("Task starts.", "B")
        self.log_history.append({"time": GetTime(), "details": "task start"})
        # Initial hardware checks
        yield "ShortPulse"
        yield "CheckCamera"

        timer = 0  # Tracks elapsed time in seconds

        def get_value(tmp_value):
            """
            Calculates a value, treating a list as a range for a random sample.

            Returns:
                float: The calculated value, rounded to 3 decimal places.
            """
            if isinstance(tmp_value, list):
                if len(tmp_value) == 2:
                    # If tmp_value is a length 2 list, sample from a uniform distribution [min, max]
                    rx = np.random.uniform(*tmp_value)
                elif len(tmp_value) == 4 and tmp_value[2] == "exp":
                    # If tmp_value is a length 4 list with "exp" as the third element, sample from an exponential distribution [min, max, "exp", lam]
                    L = tmp_value[1] - tmp_value[0]  # Length of the interval
                    u = np.random.rand()
                    factor = 1-np.exp(-tmp_value[3] * L)
                    rx = tmp_value[0] - np.log(1 - u * factor) / tmp_value[3]
                else:
                    raise ValueError(f"Invalid value format: {tmp_value}")
            else:
                rx = float(tmp_value)
            return np.round(rx, 3)

        def recursive_run(tmp_list: List):
            """Recursively processes the task structure, executing actions based on keywords."""
            nonlocal timer
            tmp_key, tmp_value = tmp_list

            # --- Task Structure Keywords ---

            if tmp_key == "Timeline":
                for tmp_time_list in tmp_value:
                    yield from recursive_run(tmp_time_list)

            elif tmp_key == "Sleep":
                sleep_duration = get_value(tmp_value)
                timer += sleep_duration
                # Log longer sleeps for better traceability
                if sleep_duration >= 5:
                    cprint(f"Sleep {sleep_duration:.1f}s.", "M")
                time.sleep(sleep_duration)

            elif tmp_key == "Trials":
                # Executes a block of trials for a specified total duration
                trials_session_start = timer
                trial_cnt = 0
                while timer < trials_session_start + tmp_value["total_duration"]:
                    trial_cnt += 1
                    cprint(f"\nTrial #{trial_cnt}", "Y")
                    yield "TrialPulse"
                    self.log_history.append({"time": GetTime(), "details": "TrialOn"})
                    yield from recursive_run(tmp_value["trial_content"])
                    yield "RegisterBehavior"  # Save behavior data after each trial

            elif tmp_key == "Choice":
                # Probabilistically selects and executes one of several branches
                choice_hash_key = get_short_hash(tmp_value)
                stream_id = self.stream_dict.setdefault(choice_hash_key, len(self.stream_dict))
                rx = self.rng.random_from_stream(stream_id)

                probs = [tmp_choice[0] for tmp_choice in tmp_value]
                assert sum(probs) == 1.0, "Probabilities in 'Choice' must sum to 1."
                choice_index = np.searchsorted(np.cumsum(probs), rx)
                
                print(f"Choice: {rx:.3f}, Stream {stream_id}, Compared to {probs}, Chose {choice_index}th option.")
                yield from recursive_run(tmp_value[int(choice_index)][1])

            elif tmp_key == "Response":
                # Waits for a response (e.g., lick) within a time window
                response_window_start = timer
                start_history_len = len(self.lick_detector.history)  # type: ignore
                while timer < response_window_start + tmp_value["total_duration"]:
                    time.sleep(Config.RESPONSE_WINDOW_CHECKING_DT)
                    timer += Config.RESPONSE_WINDOW_CHECKING_DT
                    if len(self.lick_detector.history) > start_history_len:  # type: ignore
                        uprint("-lick-")
                        self.log_history.append(
                            {"time": GetTime(), "details": "ResponseTrigger"}
                        )
                        yield from recursive_run(tmp_value["lick"])
                        break  # Exit loop after response
                else:
                    # Executes only if the while loop completes without a 'break' (no response)
                    uprint("-no-lick-")
                    self.log_history.append(
                        {"time": GetTime(), "details": "ResponseTimeOut"}
                    )
                    yield from recursive_run(tmp_value["no-lick"])

            # --- Hardware/Action Keywords ---

            elif tmp_key in {
                "Water",
                "NoWater",
            }:
                # Activates water solenoid for a specified duration
                tmp_duration = get_value(tmp_value) if Config.UNIVERSAL_WATER_VOLUME is None else Config.UNIVERSAL_WATER_VOLUME
                timer += tmp_duration
                uprint(f"-{tmp_key}-")
                self.log_history.append({"time": GetTime(), "details": f"{tmp_key}On"})
                yield f"{tmp_key}On"
                time.sleep(tmp_duration)
                yield f"{tmp_key}Off"
                self.log_history.append({"time": GetTime(), "details": f"{tmp_key}Off"})

            elif tmp_key in {
                "VerticalPuff",
                "HorizontalPuff",
                "Blank",
                "PeltierLeft",
                "PeltierRight",
                "PeltierBoth",
                "FakeRelay",
            }:
                # Activates a device for a specified duration
                tmp_duration = get_value(tmp_value)
                timer += tmp_duration
                uprint(f"-{tmp_key}-")
                self.log_history.append({"time": GetTime(), "details": f"{tmp_key}On"})
                yield f"{tmp_key}On"
                time.sleep(tmp_duration)
                yield f"{tmp_key}Off"
                self.log_history.append({"time": GetTime(), "details": f"{tmp_key}Off"})

            elif "Buzzer" in tmp_key:
                freq2play = int(tmp_key[6:]) if len(tmp_key) > 6 else Config.PURETONE_HZ
                yield f"BuzzerTune {freq2play}"

                # Activates a device for a specified duration
                tmp_duration = get_value(tmp_value)
                timer += tmp_duration
                uprint(f"-{tmp_key}-")
                self.log_history.append({"time": GetTime(), "details": f"{tmp_key}On"})
                yield f"BuzzerOn"
                time.sleep(tmp_duration)
                yield f"BuzzerOff"
                self.log_history.append({"time": GetTime(), "details": f"{tmp_key}Off"})

            elif tmp_key == "LED":
                color, control = tmp_value
                color = color.lower()
                if isinstance(control, str):
                    assert control in ("On", "Off"), f"Invalid LED control: {control}"
                    if control == "On":
                        uprint(f"-{color}LED-")
                    self.log_history.append({"time": GetTime(), "details": f"{color}LED{control}"})
                    yield f"{color}LED{control}"
                else:
                    tmp_duration = get_value(control)
                    timer += tmp_duration
                    uprint(f"-{color}LED-")
                    self.log_history.append({"time": GetTime(), "details": f"{color}LEDOn"})
                    yield f"{color}LEDOn"
                    time.sleep(tmp_duration)
                    yield f"{color}LEDOff"
                    self.log_history.append({"time": GetTime(), "details": f"{color}LEDOff"})
            elif tmp_key in ("Pass",):
                pass
            else:
                raise NotImplementedError(f"Json command {tmp_key} Not Implemented!")

        # Start the recursive execution from the top-level configuration
        yield from recursive_run(self.module_json["task_content"])

        self.log_history.append({"time": GetTime(), "details": "task end"})
        yield "RegisterBehavior"
        cprint("Task ends.", "B")

    def archive(self):
        """Write accumulated task log data to CSV file and clear history buffer."""
        tmp_snapshot = deepcopy(self.log_history)
        self.writer.write_multiple(tmp_snapshot)
        self.log_history = self.log_history[len(tmp_snapshot) :]


def GetModules(module_name: str, exp_name: str, **kwargs) -> TaskInstance:
    """Load and create task instance from JSON module file.

    Searches the task directory for a JSON file matching the module name
    and creates a TaskInstance with the loaded configuration.

    Args:
        module_name: Name of the task module to load (without .json extension).
        exp_name: Experiment name for data file naming.
        **kwargs: Additional arguments passed to TaskInstance constructor.

    Returns:
        Configured TaskInstance ready for execution.

    Raises:
        FileNotFoundError: If no matching module file is found.
    """
    for dirpath, _, filenames in os.walk(Config.TASK_DIR):
        for filename in filenames:
            if (
                filename[-5:] == ".json"
                and filename[:-5].casefold() == module_name.casefold()
            ):
                with open(path.join(dirpath, filename), "r") as file:
                    module_json = json.load(file)
                    return TaskInstance(
                        module_json=module_json, exp_name=exp_name, **kwargs
                    )
    raise FileNotFoundError(f"Module {module_name} not found in {Config.TASK_DIR}.")


if __name__ == "__main__":
    x = GetModules("Prederr_CL_Omit", "test_file")

    t0 = time.time()
    for _command in x.run():
        print(time.time() - t0, _command)
