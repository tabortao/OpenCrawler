import os
import glob

output_dir = "output"
files = glob.glob(os.path.join(output_dir, "*福田*"))
if files:
    with open(files[0], "r", encoding="utf-8") as f:
        content = f.read(5000)
        print(content)
