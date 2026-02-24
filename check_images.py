import os
import glob
import re

output_dir = "output"
files = sorted(glob.glob(os.path.join(output_dir, "*福田*.md")), key=os.path.getmtime, reverse=True)
if files:
    with open(files[0], "r", encoding="utf-8") as f:
        content = f.read()
        print("File:", files[0])
        print("Content length:", len(content))
        
        imgs = re.findall(r'!\[[^\]]*\]\([^)]+\)', content)
        print("Images found:", len(imgs))
        for img in imgs[:5]:
            print(img[:100])

images_dir = os.path.join(output_dir, "images")
if os.path.exists(images_dir):
    print("\nImages directory contents:")
    for f in os.listdir(images_dir):
        print(f)
else:
    print("\nImages directory does not exist!")
