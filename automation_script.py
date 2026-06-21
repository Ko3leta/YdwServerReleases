import os
import json
import hashlib
import zipfile
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(ROOT, "index.json")

STABLE = os.path.join(ROOT, "Channels", "Stable")
LATEST = os.path.join(ROOT, "Channels", "Latest")

STABLE_RAW = os.path.join(STABLE, "Raw")
LATEST_RAW = os.path.join(LATEST, "Raw")

STABLE_PACKED = os.path.join(STABLE, "Packed")
LATEST_PACKED = os.path.join(LATEST, "Packed")

def load_index():
    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_index(data):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def iter_files(base):
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != "Packed"]
        for file in files:
            yield os.path.join(root, file)

def relpath(base, path):
    return os.path.relpath(path, base)

def make_zip(source_dir, out_zip):
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_STORED) as z:
        for file_path in iter_files(source_dir):
            arc = relpath(source_dir, file_path)
            z.write(file_path, arc)

def update_index(channel, name, version, url, hashv, size_bytes):
    idx = load_index()
    idx[f"{channel}_name"] = name
    idx[f"{channel}_size"] = size_bytes
    idx[f"{channel}_version"] = version
    idx[f"{channel}_url"] = url
    idx[f"{channel}_hash"] = hashv
    save_index(idx)

def pack(channel):
    version = input("Enter version: ").strip()
    name = f"YDWS-{channel.upper()}-{version}"

    base = STABLE_RAW if channel == "stable" else LATEST_RAW
    packed = STABLE_PACKED if channel == "stable" else LATEST_PACKED

    os.makedirs(packed, exist_ok=True)

    zip_name = f"{name}.zip"
    zip_path = os.path.join(packed, zip_name)

    make_zip(base, zip_path)

    h = md5_file(zip_path)
    size = os.path.getsize(zip_path)

    update_index(channel, zip_name, version, "", h, size)

    print("Done. Archive created:")
    print(zip_path)
    print("MD5:", h)
    print("Size (bytes):", size)

def build_map(base):
    result = {}
    for f in iter_files(base):
        result[relpath(base, f)] = md5_file(f)
    return result

def compare():
    sm = build_map(STABLE_RAW)
    lm = build_map(LATEST_RAW)

    keys = sorted(set(sm.keys()) | set(lm.keys()))
    diffs = []

    for k in keys:
        if k not in sm:
            diffs.append(f"Missing in Stable: {k}")
        elif k not in lm:
            diffs.append(f"Missing in Latest: {k}")
        elif sm[k] != lm[k]:
            diffs.append(f"Different hash: {k}")

    if not diffs:
        print("No differences found.")
    else:
        for d in diffs:
            print(d)

def merge(src, dst):
    for f in iter_files(src):
        rel = relpath(src, f)
        target = os.path.join(dst, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(f, target)
    print("Merge completed.")

def menu():
    while True:
        print("\n=== FILE MANAGER ===")
        print("1. Pack Stable")
        print("2. Pack Latest")
        print("3. Compare Stable vs Latest")
        print("4. Merge Latest into Stable")
        print("5. Merge Stable into Latest")
        print("0. Exit")

        choice = input("Select action: ").strip()

        if choice == "1":
            pack("stable")
        elif choice == "2":
            pack("latest")
        elif choice == "3":
            compare()
        elif choice == "4":
            merge(LATEST_RAW, STABLE_RAW)
        elif choice == "5":
            merge(STABLE_RAW, LATEST_RAW)
        elif choice == "0":
            break
        else:
            print("Invalid selection")

if __name__ == "__main__":
    menu()