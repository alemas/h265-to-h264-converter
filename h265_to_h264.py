from genericpath import isdir, isfile
from importlib.resources import path
import sys
import os
import concurrent.futures as cf
import datetime
import subprocess

usage_message = f'''\nUSAGE: python3 {sys.argv[0]} -i <dir_path|file_path> [-f format] [-t tune]\n
f: video file format (default is mp4)
t: \n  film – use for high quality movie content; lowers deblocking
  animation – good for cartoons; uses higher deblocking and more reference frames
  grain – preserves the grain structure in old, grainy film material
  stillimage – good for slideshow-like content
  fastdecode – allows faster decoding by disabling certain filters
  zerolatency – good for fast encoding and low-latency streaming'''

directory_path = ""
file = ""
format = "mp4"
tune = None
begin_time = datetime.datetime.now()

def exit_with_message(message):
    print(message)
    exit()

def parse_path_input(input):
    global directory_path, file
    path = os.path.abspath(input)
    if os.path.isdir(path):
        directory_path = path
    elif os.path.isfile(path):
        file = path
    else:
        exit_with_message(f"Invalid directory/file path (-i {input})")

def parse_format_input(input):
    global format
    if input in ["mp4", "mkv"]:
        format = input
    else:
        exit_with_message(f"Invalid format (-f {input})")

def parse_tune_input(input):
    global tune
    if input in ["film", "animation", "grain", "stillimage", "fastdecode", "zerolatency"]:
        tune = input
    else:
        exit_with_message(f'''Invalid tune (-t {input})\nAvailable values are:\nfilm – use for high quality movie content; lowers deblocking
animation – good for cartoons; uses higher deblocking and more reference frames
grain – preserves the grain structure in old, grainy film material
stillimage – good for slideshow-like content
fastdecode – allows faster decoding by disabling certain filters
zerolatency – good for fast encoding and low-latency streaming''')

def parse_args():
    args = sys.argv
    if len(args) == 1:
        exit_with_message(usage_message)
    for index, arg in enumerate(args[1:]):
        if arg == "-i":
            parse_path_input(args[index+2])
        elif arg == "-f":
            parse_format_input(args[index+2])
        elif arg == "-t":
            parse_tune_input(args[index+2])
        elif arg.startswith("-"):
            exit_with_message(usage_message)

def convert_to_h264(filename, file_directory):
    output_filename = f"h264_{filename}"
    input_path = os.path.join(file_directory, filename)
    output_path = os.path.join(file_directory, output_filename)
    cmd = ["ffmpeg", "-i", input_path, "-map", "0", "-c:v", "libx264", "-crf", "18", "-tune", "animation", "-vf", "format=yuv420p", "-c:a", "copy", "-c:s", "copy"]
    if not tune is None:
        cmd += ["-tune", tune]
    cmd.append(output_path)
    result = subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    return f"\033[92m{filename} converted\033[0m" if result == 0 else f"\033[91mFailed to convert {filename}\033[0m"

futures = []

def submit_convert_process(executor, filename, file_dir):
    global futures
    future = executor.submit(convert_to_h264, filename, file_dir)
    future.add_done_callback(print_process_result)
    futures.append(future)

def print_process_result(future):
    result = future.result()
    print(result)
    print(f"Elapsed time: {datetime.datetime.now() - begin_time}")


parse_args()

with cf.ThreadPoolExecutor(max_workers=1) as executor:
    if directory_path != "":
        filename_list = []
        for filename in os.listdir(directory_path):
            f = os.path.join(directory_path, filename)
            if os.path.isfile(f) and filename.lower().endswith(f".{format}"):
                filename_list.append(filename)    
        if len(filename_list) == 0:
            exit_with_message(f"Couldn't find a {format} file on the specified path")
        for filename in filename_list:
            submit_convert_process(executor, filename, directory_path)
    elif file != "":
        directory_path = os.path.dirname(file)
        filename = os.path.basename(file)
        if filename.lower().endswith(f".{format}"):
            submit_convert_process(executor, filename, directory_path)
        else:
            exit_with_message(f"File is not of type {format}")

cf.wait(futures)
print(f"\033[94mTOTAL Elapsed time: {datetime.datetime.now() - begin_time}\033[0m")