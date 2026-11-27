  
import ctypes, random, shutil
from ctypes import wintypes as wt
from datetime import datetime
from pathlib import Path

# ---------- SET THESE ----------
INPUT_DIR  = r"L:\pq_defect"
OUTPUT_DIR = r"L:\pq_defect_updated"
SEED       = 42
# -------------------------------

EXTS  = {".bmp", ".png", ".jpg", ".jpeg"}
START = datetime(2026, 10, 28, 17, 23, 58)
END   = datetime(2026, 10, 28, 17, 40, 11)

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
        dst = out / src.name
        shutil.copy2(src, dst)
        new_dt = datetime.fromtimestamp(START.timestamp() + off)
        set_all_times(dst, new_dt)

    print(f"Done: {n} images copied to {out} with updated date/time")

if __name__ == "__main__":
    main()