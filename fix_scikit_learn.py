#!/usr/bin/env python3
import sys

import os

# Current working directory
cwd = os.getcwd()

# Path to your generated script
script_path = os.path.join(cwd, 'install/publish_dist/lib/publish_dist/publiusher')

new_line = "sys.path.insert(0, '/cs-share/pradalier/venv/tf-cpu-ros2/lib/python3.12/site-packages/')\n"

# Read the original file
with open(script_path, 'r') as f:
    lines = f.readlines()

# Replace line 5 (index 4)
if len(lines) >= 5:
    lines[4] = new_line
else:
    # If file has less than 5 lines, just append
    lines.append(new_line)

# Write back
with open(script_path, 'w') as f:
    f.writelines(lines)

print(f"Replaced line 5 in {script_path}")