
import ctypes, random, re, shutil
from ctypes import wintypes as wt
from datetime import datetime
from pathlib import Path

# ---------- SET THESE ----------
INPUT_DIR  = r"L:\oq_good"
OUTPUT_DIR = r"L:\oq_good_updated"
SEED       = 42
# # -------------------------------
# 27th Oct 26 12:00:00 to 16:00:00-

EXTS  = {".bmp", ".png", ".jpg", ".jpeg"}
START = datetime(2026, 10, 26, 12, 00, 00)
END   = datetime(2026, 10, 27, 16, 00, 00)

k32 = ctypes.windll.kernel32
k32.CreateFileW.restype = wt.HANDLE
k32.CreateFileW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD, wt.LPVOID,
                            wt.DWORD, wt.DWORD, wt.HANDLE]
k32.SetFileTime.argtypes = [wt.HANDLE, ctypes.POINTER(wt.FILETIME),
                            ctypes.POINTER(wt.FILETIME), ctypes.POINTER(wt.FILETIME)]
k32.CloseHandle.argtypes = [wt.HANDLE]

def set_all_times(path, dt):
    t = int((dt.timestamp() + 11644473600) * 10_000_000)
    ft = wt.FILETIME(t & 0xFFFFFFFF, t >> 32)
    h = k32.CreateFileW(str(path), 0x100, 0, None, 3, 0x80, None)  # FILE_WRITE_ATTRIBUTES
    if h in (None, wt.HANDLE(-1).value):
        raise OSError(f"Cannot open {path}")
    k32.SetFileTime(h, ctypes.byref(ft), ctypes.byref(ft), ctypes.byref(ft))
    k32.CloseHandle(h)

def list_imgs(folder):
    return sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in EXTS)

def new_name(old_name, new_dt):
    stamp = new_dt.strftime("%Y%m%d_%H%M%S")
    # replace leading YYYYMMDD_HHMMSS with the new stamp, keep the rest (_xxxxxx_OK.bmp etc.)
    if re.match(r"^\d{8}_\d{6}_", old_name):
        return re.sub(r"^\d{8}_\d{6}_", stamp + "_", old_name)
    # fallback: filename doesn't match the expected pattern, just prefix it
    return f"{stamp}_{old_name}"

def main():
    random.seed(SEED)
    files = list_imgs(INPUT_DIR)
    n = len(files)
    if n == 0:
        print("No images found in INPUT_DIR")
        return

    span = (END - START).total_seconds()
    offsets = sorted(random.uniform(0, span) for _ in range(n))
    offsets[0], offsets[-1] = 0, span   # exact start / end

    out = Path(OUTPUT_DIR)
    out.mkdir(parents=True, exist_ok=True)

    for src, off in zip(files, offsets):
        new_dt = datetime.fromtimestamp(START.timestamp() + off)
        dst_name = new_name(src.name, new_dt)
        dst = out / dst_name
        if dst.exists():
            dst = out / f"{dst.stem}_dup{dst.suffix}"
        shutil.copy2(src, dst)
        set_all_times(dst, new_dt)

    print(f"Done: {n} images copied to {out} with updated date/time and filenames")

if __name__ == "__main__":
    main()