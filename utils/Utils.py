import time
import re
import numpy as np
from colorist import Color, BrightColor


def GetTime():
    return time.monotonic_ns()/1e6


# Trial Symbols
UNICODE_TRIAL = {
    "VerticalPuff": f"--\x1b[42m ↓ Puff \x1b[0m--",
    "Blank": f"\x1b[41mBlank\x1b[0m",
    "HorizontalPuff": f"---\x1b[43m →  Puff \x1b[0m---",
    "NoWater": f"\x1b[100mNoWater\x1b[0m",
    "Water": f"\x1b[104mWater\x1b[0m",
    "Sleep": f"\x1b[90mSleep\x1b[0m",
    "Buzzer": f"\x1b[46mBuzzer\x1b[0m",
}


def uprint(raw_string):
    for key in UNICODE_TRIAL.keys():
        raw_string = raw_string.replace(f"-{key}-", f"-{UNICODE_TRIAL[key]}-")
    print(raw_string)


def cprint(flag, c=None):
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


def vis_water(water_prob):
    n_num = int(water_prob*10)
    return f"\x1b[94m"+" "*9+"█"*n_num +f"\x1b[0m\x1b[90m"+"█"*(10-n_num)+" "*9+f"\x1b[0m"


def len_nocolor(colored_s: str):
    return len(re.sub(r'\x1b\[[0-9;]*[mG]', '', colored_s))


def tab_block(*args, sub_char=" ", centering=True):
    n_char = np.max([len_nocolor(s) for s in args])
    # n_tabs = int(np.ceil(n_char/4))
    # new_s = [s+"\t"*(n_tabs - int(np.floor(len_nocolor(s)/4))) for s in args]
    new_s = []
    for s in args:
        half_len = int((n_char - len_nocolor(s))/2)
        if centering:
            new_s.append(sub_char*half_len+s+sub_char*(n_char-len_nocolor(s)-half_len))
        else:
            new_s.append(sub_char*(n_char-len_nocolor(s))+s)
    return sub_char*n_char, *new_s
