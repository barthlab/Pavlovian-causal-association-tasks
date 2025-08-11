import time
import re
from typing import List, Tuple
import numpy as np
from colorist import Color


def GetTime() -> float:
    """Get current time in milliseconds using monotonic clock.

    Returns:
        Current time in milliseconds as a float.
    """
    return time.monotonic_ns()/1e6


# Trial Symbols
UNICODE_TRIAL = {
    "VerticalPuff": "--\x1b[42m ↓ Puff \x1b[0m--",
    "Blank": "\x1b[41mBlank\x1b[0m",
    "HorizontalPuff": "---\x1b[43m → Puff \x1b[0m---",
    "PeltierLeft": "-\x1b[44m Left  ■ \x1b[0m-",
    "PeltierRight": "-\x1b[44m Right  ■ \x1b[0m-",
    "PeltierBoth": "-\x1b[44m Both  ■ \x1b[0m-",
    "NoWater": "\x1b[100mNoWater\x1b[0m",
    "Water": "\x1b[104mWater\x1b[0m",
    "Sleep": "\x1b[90mSleep\x1b[0m",
    "Buzzer": "\x1b[45mBuzzer\x1b[0m",
    "no-lick": "\x1b[31mno-lick\x1b[0m",
    "lick": "\x1b[32mlick\x1b[0m",
}


def uprint(raw_string: str):
    """Print string with Unicode trial symbols replaced by colored versions.

    Replaces trial symbol placeholders (e.g., "-VerticalPuff-") with their
    corresponding colored Unicode representations defined in UNICODE_TRIAL.

    Args:
        raw_string: String containing trial symbol placeholders to replace.
    """
    for key in UNICODE_TRIAL.keys():
        raw_string = raw_string.replace(f"-{key}-", f"-{UNICODE_TRIAL[key]}-")
    print(raw_string)


def cprint(flag: str, c: str = ""):
    """Print colored text using colorist library.

    Args:
        flag: Text to print.
        c: Color code - "R" (red), "B" (blue), "G" (green), "Y" (yellow),
           "M" (magenta), "C" (cyan), or empty string for no color.
    """
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


def vis_water(water_prob: float) -> str:
    """Generate visual representation of water probability.

    Creates a colored bar showing water delivery probability as filled blocks.

    Args:
        water_prob: Probability value between 0.0 and 1.0.

    Returns:
        ANSI colored string representing the probability as a visual bar.
    """
    n_num = int(water_prob*10)
    return "\x1b[94m"+" "*9+"█"*n_num + "\x1b[0m\x1b[90m"+"█"*(10-n_num)+" "*9+"\x1b[0m"


def len_nocolor(colored_s: str) -> int:
    """Calculate string length excluding ANSI color codes.

    Args:
        colored_s: String that may contain ANSI color escape sequences.

    Returns:
        Length of the string with color codes removed.
    """
    return len(re.sub(r'\x1b\[[0-9;]*[mG]', '', colored_s))


def tab_block(*args: str, sub_char: str = " ", centering: bool = True, alignment: str = "left") -> Tuple[str, ...]:
    """Create aligned text blocks with consistent width.

    Formats multiple strings to have the same width using padding characters,
    with options for centering or alignment.

    Args:
        *args: Strings to format into aligned blocks.
        sub_char: Character to use for padding (default: space).
        centering: Whether to center text within blocks.
        alignment: Text alignment when not centering ("left" or "right").

    Returns:
        Tuple containing a separator line followed by the formatted strings.

    Raises:
        NotImplementedError: If alignment is not "left" or "right".
    """
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
