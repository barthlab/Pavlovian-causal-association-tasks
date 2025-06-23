import time
import re
from typing import List, Tuple
import numpy as np
from colorist import Color


def GetTime():
    return time.monotonic_ns()/1e6


# Trial Symbols
UNICODE_TRIAL = {
    "VerticalPuff": "--\x1b[42m ↓ Puff \x1b[0m--",
    "Blank": "\x1b[41mBlank\x1b[0m",
    "HorizontalPuff": "---\x1b[43m →  Puff \x1b[0m---",
    "NoWater": "\x1b[100mNoWater\x1b[0m",
    "Water": "\x1b[104mWater\x1b[0m",
    "Sleep": "\x1b[90mSleep\x1b[0m",
    "Buzzer": "\x1b[45mBuzzer\x1b[0m",
    "no-lick": "\x1b[31mno-lick\x1b[0m",
    "lick": "\x1b[32mlick\x1b[0m",
}


def uprint(raw_string: str):
    for key in UNICODE_TRIAL.keys():
        raw_string = raw_string.replace(f"-{key}-", f"-{UNICODE_TRIAL[key]}-")
    print(raw_string)


def cprint(flag: str, c: str = ""):
    if c == "R":
        print(f"{Color.RED}{flag}{Color.OFF}")
    elif c == "B":
        print(f"{Color.BLUE}{flag}{Color.OFF}")
    elif c == "G":
        print(f"{Color.GREEN}{flag}{Color.OFF}")
    elif c == "Y":
        print(f"{Color.YELLOW}{flag}{Color.OFF}")
    elif c == "M":
        print(f"{Color.MAGENTA}{flag}{Color.OFF}")
    elif c == "C":
        print(f"{Color.CYAN}{flag}{Color.OFF}")
    else:
        print(f"{flag}")


def vis_water(water_prob: float):
    n_num = int(water_prob*10)
    return "\x1b[94m"+" "*9+"█"*n_num + "\x1b[0m\x1b[90m"+"█"*(10-n_num)+" "*9+"\x1b[0m"


def len_nocolor(colored_s: str):
    return len(re.sub(r'\x1b\[[0-9;]*[mG]', '', colored_s))


def tab_block(*args: str, sub_char: str = " ", centering: bool = True, alignment: str = "left") -> Tuple[str, ...]:
    n_char = np.max([len_nocolor(s) for s in args])
    # n_tabs = int(np.ceil(n_char/4))
    # new_s = [s+"\t"*(n_tabs - int(np.floor(len_nocolor(s)/4))) for s in args]
    new_s: List[str] = []
    for s in args:
        half_len = int((n_char - len_nocolor(s))/2)
        if centering:
            new_s.append(sub_char*half_len+s+sub_char *
                         (n_char-len_nocolor(s)-half_len))
        elif alignment == "left":
            new_s.append(s+sub_char*(n_char-len_nocolor(s)))
        elif alignment == "right":
            new_s.append(sub_char*(n_char-len_nocolor(s))+s)
        else:
            raise NotImplementedError
    return sub_char*n_char, *new_s
