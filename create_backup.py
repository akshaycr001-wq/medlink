"""Create a complete zip backup of the MedLink project."""
import zipfile
import os
import datetime

src = r"c:\Users\eldho\Downloads\Templatefolder"
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
dest = rf"c:\Users\eldho\Downloads\MedLink_Backup_{timestamp}.zip"

skip_dirs = {"__pycache__", ".git", ".ipynb_checkpoints", "node_modules"}
skip_ext = {".zip"}

count = 0
skipped = []

with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(src):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for f in files:
            if os.path.splitext(f)[1].lower() in skip_ext:
                continue
            full = os.path.join(root, f)
            arcname = os.path.relpath(full, src)
            try:
                zf.write(full, arcname)
                count += 1
            except (PermissionError, OSError) as e:
                skipped.append((arcname, str(e)))

print(f"Backup created: {dest}")
print(f"Files archived: {count}")
if skipped:
    print(f"Skipped {len(skipped)} files (locked):")
    for name, err in skipped:
        print(f"  - {name}")
else:
    print("No files were skipped. Complete backup!")

# Show file size
size_mb = os.path.getsize(dest) / (1024 * 1024)
print(f"Backup size: {size_mb:.1f} MB")
