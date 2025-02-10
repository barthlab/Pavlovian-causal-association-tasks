# convert .h264 video to .avi video
import os
import sys
import time
import os.path as path
from glob import glob
import subprocess
from Config import SAVE_DIR

for dir_path, _ , _ in os.walk(SAVE_DIR):
    for file_path in glob(path.join(dir_path, "*.h264")):
        tmp_dir, tmp_file = path.dirname(file_path), path.basename(file_path)
        output_file = file_path.replace(".h264", ".avi")
        print(output_file)
        if path.exists(output_file):
            continue
        command = (r"ffmpeg -framerate 30 -i {} -q:v 6 -vf fps=30 "
                   r"-hide_banner -loglevel warning {}").format(file_path, output_file)
        print(command)
        time_start = time.time()
        try:
            subprocess.run(command, check=True, shell=True)
            print(f"Conversion successful: {output_file}, takes {time.time()-time_start:.2f}s")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")