import time
import os
import os.path
import json
import re
import random
import numpy as np
# from scipy.stats import qmc
from copy import copy, deepcopy
from typing import List
from utils.Logger import CSVFile
from utils.Utils import *
# from tools.LickDetector import *
from Config import *


class TaskInstance:
    def __init__(self, module_json, exp_name):
        self.log_history = []

        self.module_json = module_json
        self.task_name = self.module_json['task_name']

        self.writer = CSVFile(path.join(SAVE_DIR, f"TIMELINE_{exp_name}.csv"), ["time", "details"])
        self.vis()
        exit()

    def read_task_json(self):

        if "task_rng" not in self.module_json or self.module_json['task_rng'] == "default":
            random_pool = np.random.uniform(0, 1, 1000)
        else:
            raise NotImplementedError(f"RNG {self.module_json['task_rng']}Not Implemented!")
        timer = 0
        self.tape = []

        def get_value(tmp_value):
            rx = np.random.uniform(*tmp_value) if isinstance(tmp_value, list) else float(tmp_value)
            return np.round(rx, 3)

        def recursive_read(tmp_list: list):
            nonlocal timer
            tmp_key, tmp_value = tmp_list
            if tmp_key == "Timeline":
                for tmp_timeline_list in tmp_value:
                    recursive_read(tmp_timeline_list)
            elif tmp_key == "Sleep":
                sleep_duration = get_value(tmp_value)
                timer += sleep_duration
                self.tape.append(["Sleep", sleep_duration])
            elif tmp_key == "Trials":
                prev_timer = timer + 0
                trial_cnt = 0
                while timer < prev_timer + tmp_value['total_duration']:
                    trial_cnt += 1
                    self.tape.append(["Trial", trial_cnt])
                    recursive_read(tmp_value['trial_content'])
                self.tape.append(["TrialEnd", None])
            elif tmp_key == "Choice":
                probs = [tmp_choice[0] for tmp_choice in tmp_value]
                assert sum(probs) == 1.
                choice_index = np.random.choice(len(tmp_value), p=probs)
                recursive_read(tmp_value[int(choice_index)][1])
            elif tmp_key in ("Buzzer", "VerticalPuff", "HorizontalPuff", "Blank", "Water", "NoWater"):
                tmp_duration = get_value(tmp_value)
                timer += tmp_duration
                self.tape.append([tmp_key, tmp_duration])
            else:
                raise NotImplementedError(f"Json command {tmp_key} Not Implemented!")
        recursive_read(self.module_json['task_content'])

    def vis(self):
        """Generates and prints an ASCII art representation of the task structure."""
        print(self.module_json['task_name'])

        def recursive_paint(tmp_list: List[str]) -> List[str]:
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
                max_width = sum(len(block[0]) for block in result_blocks) + len(result_blocks) + 1

                # Create a blank canvas and paste each component side-by-side,
                # centered vertically within the timeline.
                final_blocks = [" " * max_width for _ in range(max_height)]
                width_ptr = 1
                for block in result_blocks:
                    height, width = len(block), len(block[0])
                    start_height = (max_height - height) // 2
                    for i, row_content in enumerate(block):
                        row_idx = start_height + i
                        final_blocks[row_idx] = (final_blocks[row_idx][:width_ptr] +
                                                 row_content +
                                                 final_blocks[row_idx][width_ptr + width:])
                    width_ptr += width + 1

            # --- Trials: A repeating container ---
            elif tmp_key == "Trials":
                # Render the inner content and wrap it in a container labeled "N x"
                # to signify a repeating trial.
                result_block = recursive_paint(tmp_value['trial_content'])
                new_strings = tab_block(*result_block, f"{tmp_value['total_duration']} s", sub_char="-")

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

                for i, (prob_str, block) in enumerate(zip(sync_prob_strings, result_blocks)):
                    _, *sync_strings, _ = tab_block(*block, " " * max_width, centering=False)
                    new_strings = [" "*(len(prob_str) + 1) + single_sync_string for single_sync_string in sync_strings]
                    center_height = len(new_strings) // 2
                    new_strings[center_height] = f" {prob_str}{new_strings[center_height][1 + len(prob_str):]}"

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
                lick_blocks = recursive_paint(tmp_value['lick'])
                no_lick_blocks = recursive_paint(tmp_value['no-lick'])
                max_width = max(len(lick_blocks[0]), len(no_lick_blocks[0]))

                _, *response_strings = tab_block('-lick-', '-no-lick-')

                for i, (resp_str, block) in enumerate(zip(response_strings, [lick_blocks, no_lick_blocks])):
                    _, *sync_strings, _ = tab_block(*block, " " * max_width, centering=False)
                    new_strings = [" "*(len(resp_str) + 1) + single_sync_string for single_sync_string in sync_strings]
                    center_height = len(new_strings) // 2
                    new_strings[center_height] = f" {resp_str}{new_strings[center_height][1 + len(resp_str):]}"

                    # Draw vertical connector lines.
                    if i == 0:  # Top (lick) branch
                        for row in range(center_height, len(new_strings)):
                            new_strings[row] = f"|{new_strings[row][1:]}"
                    if i == 1:  # Bottom (no-lick) branch
                        for row in range(center_height + 1):
                            new_strings[row] = f"|{new_strings[row][1:]}"
                    final_blocks.extend(new_strings)

            # --- Base Cases: Simple timed events ---
            elif tmp_key in ("Sleep", "Buzzer", "VerticalPuff", "HorizontalPuff", "Blank", "Water", "NoWater"):
                # These are terminal nodes. Format the event name and duration into a
                # simple, standardized block, handling both fixed and ranged durations.
                duration_str = (f"{tmp_value} s" if not isinstance(tmp_value, list)
                                else f"{tmp_value[0]}~{tmp_value[1]} s")
                _, string_key, string_duration = tab_block(f"-{tmp_key}-", f"-{duration_str}-", sub_char='-')
                final_blocks = [" " * len(string_key), string_key, string_duration]

            # --- Error Handling ---
            else:
                raise NotImplementedError(f"JSON command '{tmp_key}' is not implemented!")

            # Sanity check to ensure all lines in a block have the same width.
            assert len(set(map(len, final_blocks))) == 1, \
                f"Block for '{tmp_key}' has inconsistent line widths."
            return final_blocks

        # Generate and print the final ASCII art for the entire task.
        vis_block = recursive_paint(self.module_json['task_content'])
        for vis_line in vis_block:
            uprint(vis_line)

    def vis_trial(self, tape_segment):
        line1, line2 = "", ""
        for tmp_key, tmp_value in tape_segment:
            tmp_duration = f"{tmp_value} s"
            _, string_key, string_duration = tab_block(f"-{tmp_key}-", f"-{tmp_duration}-", sub_char='-')
            line1 += string_key
            line2 += string_duration
        uprint(line1)
        uprint(line2)

    def run(self):
        self.log_history.append({"time": GetTime(), "details": "task start"})
        yield 'ShortPulse'
        yield 'CheckCamera'
        for tape_id, (key, value) in enumerate(self.tape):
            if key == "Sleep":
                if value > 10:
                    cprint(f"Sleep {value}s", "M")
                time.sleep(value)
            elif key == "Trial":
                trial_cnt = 1
                while self.tape[tape_id+trial_cnt][0] not in ("Trial", "TrialEnd"):
                    trial_cnt += 1
                cprint(f"\nTrial #{value}", "Y")
                yield 'RegisterBehavior'
                self.vis_trial(self.tape[tape_id+1: tape_id+trial_cnt])
            elif key in ("Buzzer", "VerticalPuff", "HorizontalPuff", "Blank", "Water", "NoWater"):
                uprint(f"-{key}-")
                self.log_history.append({"time": GetTime(), "details": f"{key}On"})
                yield f"{key}On"
                time.sleep(value)
                yield f"{key}Off"
                self.log_history.append({"time": GetTime(), "details": f"{key}Off"})

        self.log_history.append({"time": GetTime(), "details": "task end"})
        yield 'RegisterBehavior'

    def archive(self):
        tmp_snapshot = deepcopy(self.log_history)
        self.writer.write_multiple(tmp_snapshot)
        self.log_history = self.log_history[len(tmp_snapshot):]


def GetModules(module_name, exp_name):
    for (dirpath, dirnames, filenames) in os.walk(TASK_DIR):
        for filename in filenames:
            if filename[-5:] == ".json" and filename[:-5].casefold() == module_name.casefold():
                with open(path.join(dirpath, filename), "r") as file:
                    module_json = json.load(file)
                    return TaskInstance(module_json=module_json, exp_name=exp_name)
    raise FileNotFoundError(f"Module {module_name} Not Found in {TASK_DIR}!")


if __name__ == "__main__":
    x = GetModules("acc80passive", "test_file")

    t0 = time.time()
    for command in x.run():
        print(time.time()-t0, command)