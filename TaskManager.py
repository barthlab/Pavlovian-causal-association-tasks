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
from tools.LickDetector import *
from Config import *


class TaskInstance:
    def __init__(self, module_json, exp_name):
        self.log_history = []
        self.tape = []
        self.module_json = module_json
        self.read_task_json()
        self.writer = CSVFile(path.join(SAVE_DIR, f"TIMELINE_{exp_name}.csv"),
                              ["time", "details"])

    def read_task_json(self):
        self.task_name = self.module_json['task_name']

        if "task_rng" not in self.module_json or self.module_json['task_rng'] == "default":
            random_pool = np.random.uniform(0, 1, 1000)
        elif self.module_json['task_rng'] == "halton":
            random_pool = np.random.uniform(0, 1, 1000)
            # random_pool = qmc.Halton(d=1, scramble=True).random(1000)
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
        print(self.module_json['task_name'])
        def recursive_paint(tmp_list: List[str]) -> List[str]:
            tmp_key, tmp_value = tmp_list
            result_blocks = []
            if tmp_key == "Timeline":
                max_height, max_width = 0, 0
                for tmp_timeline_list in tmp_value:
                    result_blocks.append(recursive_paint(tmp_timeline_list))
                    max_height = max(max_height, len(result_blocks[-1]))
                    max_width += len(result_blocks[-1][0]) + 1
                max_width += 1
                final_blocks = [" "*max_width for _ in range(max_height)]
                width_ptr = 1
                center_height = int(max_height/2)
                for result_block in result_blocks:
                    result_height, result_width = len(result_block), len(result_block[0])
                    start_height = int(max_height/2 - result_height/2)
                    for tmp_row in range(start_height, start_height+result_height):
                        final_blocks[tmp_row] = (final_blocks[tmp_row][:width_ptr] +
                                                 result_block[tmp_row-start_height]+
                                                 final_blocks[tmp_row][width_ptr+result_width:])
                    width_ptr += result_width+1
                    # final_blocks[center_height] = (final_blocks[center_height][:width_ptr-1]+' '+
                    #                                final_blocks[center_height][width_ptr:])
                return final_blocks
            elif tmp_key == "Trials":
                result_block = recursive_paint(tmp_value['trial_content'])
                new_strings = tab_block(*result_block, f"{tmp_value['total_duration']} s",
                                            sub_char="-")
                max_height = len(new_strings) + 1
                max_width = len(new_strings[0]) + 7
                center_height = int(max_height / 2)
                final_blocks = [" " * max_width for _ in range(max_height)]
                for tmp_row in range(1, max_height):
                    final_blocks[tmp_row] = final_blocks[tmp_row][:5]+"|"+new_strings[tmp_row-1]+"|"
                final_blocks[center_height] = " N x " + final_blocks[center_height][5:]
                return final_blocks
            elif tmp_key == "Choice":
                result_blocks = [recursive_paint(tmp_choice[1]) for tmp_choice in tmp_value]
                max_width = np.max([len(result_block[0]) for result_block in result_blocks]) + 1
                final_blocks = []
                for choice_id, (tmp_choice, result_block) in enumerate(zip(tmp_value, result_blocks)):
                    prob = tmp_choice[0]
                    tabs, prob_string = tab_block(f"-{int(prob*100)}%-")
                    _, *new_strings, _ = tab_block(*result_block, " "*(max_width+len(prob_string)),
                                                   centering=False)
                    center_height = int(len(new_strings)/2)
                    new_strings[center_height] = " "+prob_string+new_strings[center_height][1+len(prob_string):]
                    if choice_id < len(tmp_value)-1:
                        for string_id in range(center_height, len(new_strings)):
                            new_strings[string_id] = "|" + new_strings[string_id][1:]
                    if choice_id > 0:
                        for string_id in range(center_height+1):
                            new_strings[string_id] = "|" + new_strings[string_id][1:]
                    final_blocks += new_strings
                return final_blocks
            elif tmp_key in ("Sleep", "Buzzer", "VerticalPuff", "HorizontalPuff", "Blank", "Water", "NoWater"):
                tmp_duration = f"{tmp_value} s" if not isinstance(tmp_value, list) else \
                    f"{tmp_value[0]}~{tmp_value[1]} s"
                _, string_key, string_duration = tab_block(f"-{tmp_key}-", f"-{tmp_duration}-", sub_char='-')
                return [" "*len(string_key), string_key, string_duration]
            else:
                raise NotImplementedError(f"Json command {tmp_key} Not Implemented!")
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
        self.vis()
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
    found_flag = False
    for (dirpath, dirnames, filenames) in os.walk(TASK_DIR):
        for filename in filenames:
            if filename[-5:] == ".json" and filename[:-5].casefold() == module_name.casefold():
                with open(path.join(dirpath, filename), "r") as file:
                    module_json = json.load(file)
                    found_flag = True
                    break
        if found_flag:
            break
    if not found_flag:
        raise FileNotFoundError(f"Module {module_name} Not Found in {TASK_DIR}!")
    return TaskInstance(module_json=module_json, exp_name=exp_name)


if __name__ == "__main__":
    x = GetModules("Pse50", "test_file")

    t0 = time.time()
    for command in x.run():
        print(time.time()-t0, command)