"""Video format conversion utility for experiment recordings.

Converts .h264 video files to .avi format using ffmpeg. Processes all
.h264 files found in the data directory and subdirectories.
"""

import os
import sys
import time
import os.path as path
from glob import glob
import subprocess
from Config import SAVE_DIR


def convert_videos():
    """Convert all .h264 video files to .avi format.

    Searches the data directory for .h264 files and converts them to .avi
    using ffmpeg with quality settings optimized for behavioral analysis.
    Skips files that have already been converted.
    """
    for dir_path, _ , _ in os.walk(SAVE_DIR):
        for file_path in glob(path.join(dir_path, "*.h264")):
            tmp_dir, tmp_file = path.dirname(file_path), path.basename(file_path)
            output_file = file_path.replace(".h264", ".avi")
            print(f"Processing: {output_file}")

            if path.exists(output_file):
                print("Output file already exists, skipping.")
                continue

            command = (r"ffmpeg -framerate 30 -i {} -q:v 6 -vf fps=30 "
                       r"-hide_banner -loglevel warning {}").format(file_path, output_file)
            print(f"Command: {command}")

            time_start = time.time()
            try:
                subprocess.run(command, check=True, shell=True)
                print(f"Conversion successful: {output_file}, took {time.time()-time_start:.2f}s.")
            except subprocess.CalledProcessError as e:
                print(f"Error occurred: {e}.")


if __name__ == "__main__":
    convert_videos()