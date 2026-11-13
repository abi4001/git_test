"""
convert_json_to_yolo.py
-----------------------------------------------------------
Polygon JSON  ->  YOLO segmentation TXT
  JSON read from : dataset/labels/<split>/   and  dataset/images/<split>/
  images read from: dataset/images/<split>/
  TXT saved to    : dataset/labels_txt/<split>/<image_name>.txt
                    format -> 0 x1 y1 x2 y2 ... (normalized 0-1)

Supports LabelMe / X-AnyLabeling, VIA, COCO-style and most custom polygon JSON.
COPY_TO_LABELS = True also copies each txt into dataset/labels/<split>/,
because YOLO only reads labels from a folder named "labels".
"""

import json
import shutil
from collections import Counter
from pathlib import Path
from PIL import Image

# ---------------- Settings ----------------
BASE_DIR = Path(r"L:\PROJECT_VISION\y_yolo11\dataset")
SPLITS = ["train", "val"]

OUT_NAME = "labels_txt"          # output folder name
COPY_TO_LABELS = False           # True -> also copy txt into labels/<split> for YOLO training

CLASS_ID = 0                     # trimp
CROP_X, CROP_Y = 262, 0          # crop offset, used only if polygons are in FULL-image coordinates
IMG_EXT = (".bmp", ".png", ".jpg", ".jpeg", ".tif", ".tiff")
POINT_KEYS = ("points", "polygon", "segmentation", "vertices", "coordinates", "poly")


# ---------------- JSON parsing ----------------
def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)

def _parse_points(v):
    """Return a list of polygons, each a list of (x, y), from many layouts."""
    if not isinstance(v, list) or not v:
        return []
    # [[x, y], [x, y], ...]
    if all(isinstance(p, (list, tuple)) and len(p) == 2 and all(_is_num(c) for c in p) for p in v):
        return [[(float(x), float(y)) for x, y in v]]
    # [{"x": .., "y": ..}, ...]
    if all(isinstance(p, dict) and "x" in p and "y" in p for p in v):
        return [[(float(p["x"]), float(p["y"])) for p in v]]
    # [x1, y1, x2, y2, ...]
    if all(_is_num(c) for c in v) and len(v) % 2 == 0:
        return [[(float(v[i]), float(v[i + 1])) for i in range(0, len(v), 2)]]
    # list of polygons
    out = []
    for item in v:
        out += _parse_points(item)
    return out

def extract_polygons(obj):
    polys = []
    if isinstance(obj, dict):
        if "all_points_x" in obj and "all_points_y" in obj:          # VIA
            polys.append(list(zip(map(float, obj["all_points_x"]), map(float, obj["all_points_y"]))))
        for k, v in obj.items():
            if k.lower() in POINT_KEYS:
                found = _parse_points(v)
                # rectangle (2 points) -> 4-point polygon
                if obj.get("shape_type") == "rectangle" and found and len(found[0]) == 2:
                    (x1, y1), (x2, y2) = found[0]
                    found = [[(x1, y1), (x2, y1), (x2, y2), (x1, y2)]]
                polys += found
            elif isinstance(v, (dict, list)):
                polys += extract_polygons(v)
    elif isinstance(obj, list):
        for item in obj:
            polys += extract_polygons(item)
    return [p for p in polys if len(p) >= 3]

# ---------------- Conversion ----------------
def to_yolo_line(poly, img_w, img_h):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]

    if max(xs + ys) <= 1.0:                                  # already normalized
        nx, ny = xs, ys
    else:
        if max(xs) > img_w + 1 or max(ys) > img_h + 1:       # full-image coordinates
            xs = [x - CROP_X for x in xs]
            ys = [y - CROP_Y for y in ys]
        nx = [x / img_w for x in xs]
        ny = [y / img_h for y in ys]

    clip = lambda v: min(max(v, 0.0), 1.0)
    return f"{CLASS_ID} " + " ".join(f"{clip(x):.6f} {clip(y):.6f}" for x, y in zip(nx, ny))

def main():
    for split in SPLITS:
        img_dir = BASE_DIR / "images" / split
        lbl_dir = BASE_DIR / "labels" / split
        out_dir = BASE_DIR / OUT_NAME / split

        if not img_dir.exists():
            print(f"\nERROR: image folder not found: {img_dir}")
            continue
        out_dir.mkdir(parents=True, exist_ok=True)

        images = {p.stem: p for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXT}

        search_dirs = [lbl_dir, img_dir]
        jsons = sorted({jp for d in search_dirs if d.exists() for jp in d.glob("*.json")})

        converted, n_poly, no_poly, no_img, bad = 0, 0, [], [], []
        for jp in jsons:
            try:
                data = json.loads(jp.read_text(encoding="utf-8"))
            except Exception:
                bad.append(jp.name)
                continue

            stem = jp.stem
            if stem not in images and isinstance(data, dict) and data.get("imagePath"):
                stem = Path(str(data["imagePath"]).replace("\\", "/")).stem
            if stem not in images:
                no_img.append(jp.name)
                continue
            polys = extract_polygons(data)
            if not polys:
                no_poly.append(jp.name)
                continue
            with Image.open(images[stem]) as im:
                img_w, img_h = im.size

            lines = [to_yolo_line(p, img_w, img_h) for p in polys]
            txt_path = out_dir / f"{stem}.txt"
            txt_path.write_text("\n".join(lines), encoding="utf-8")

            if COPY_TO_LABELS:
                lbl_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(txt_path, lbl_dir / txt_path.name)
            converted += 1
            n_poly += len(polys)

        print(f"\n========== {split} ==========")
        print(f"images found       : {len(images)}")
        print(f"JSON found         : {len(jsons)}")
        print(f"converted to txt   : {converted}   (polygons: {n_poly})")
        print(f"saved in           : {out_dir}")
        print(f"images with no txt : {len(images) - converted}  (good/background images)")
        if COPY_TO_LABELS:
            print(f"also copied to     : {lbl_dir}")
        if no_img:
            print(f"WARNING no matching image : {no_img[:5]}")
        if no_poly:
            print(f"WARNING no polygon found  : {no_poly[:5]}")
        if bad:
            print(f"WARNING unreadable JSON   : {bad[:5]}")
        if not jsons:
            print("NO JSON FILES FOUND. Files present:")
            for d in search_dirs:
                if d.exists():
                    exts = Counter(p.suffix.lower() for p in d.iterdir() if p.is_file())
                    print(f"   {d}: {dict(exts)}")

    print("\nDONE")
if __name__ == "__main__":
    main()