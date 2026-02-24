import os
import glob
import re

output_dir = "output"

md_files = sorted(glob.glob(os.path.join(output_dir, "*Python*3.md")), key=os.path.getmtime, reverse=True)
if md_files:
    with open(md_files[0], "r", encoding="utf-8") as f:
        content = f.read()
        print("MD File:", md_files[0])
        print("Content length:", len(content))
        
        imgs = re.findall(r'!\[[^\]]*\]\([^)]+\)', content)
        print("Images in MD:", len(imgs))
        for img in imgs:
            print(f"  - {img}")

images_dir = os.path.join(output_dir, "images")
print(f"\nChecking: {images_dir}")
if os.path.exists(images_dir):
    files = os.listdir(images_dir)
    print(f"Images directory contains {len(files)} files:")
    for f in files[:10]:
        filepath = os.path.join(images_dir, f)
        size = os.path.getsize(filepath)
        print(f"  - {f} ({size} bytes)")
else:
    print("Images directory does not exist!")
