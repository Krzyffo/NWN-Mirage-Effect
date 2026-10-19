"""Build NWN-Mirage.

  py tools/build.py            compile, pack, install the hak
  py tools/build.py --list F   print the contents of an .erf/.hak

- src/nss/*.nss are compiled with Beamdog's nwn_script_comp and packed with
  their .ncs into build/nwn_mirage.erf (File > Import in the toolset).
- src/shaders/*.shd are packed into build/nwn_mirage.hak, which is copied
  to the NWN hak folder.

Paths can be overridden with the NWN_ROOT and NWN_USER environment variables.
The compiler comes from the neverwinter.nim release, unzipped into
tools/neverwinter/ (https://github.com/niv/neverwinter.nim/releases).
"""
import datetime
import os
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NSS = os.path.join(ROOT, "src", "nss")
SHADERS = os.path.join(ROOT, "src", "shaders")
NCS = os.path.join(ROOT, "build", "ncs")
ERF_OUT = os.path.join(ROOT, "build", "nwn_mirage.erf")
HAK_OUT = os.path.join(ROOT, "build", "nwn_mirage.hak")
COMPILER = os.path.join(ROOT, "tools", "neverwinter", "nwn_script_comp.exe")
NWN_ROOT = os.environ.get("NWN_ROOT", r"G:\SteamLibrary\steamapps\common\Neverwinter Nights")
NWN_USER = os.environ.get("NWN_USER", r"G:\nwnData")  # see [Alias] HD0 in nwn.ini

RES_TYPES = {"nss": 2009, "ncs": 2010, "shd": 2069}
TYPE_EXT = {v: k for k, v in RES_TYPES.items()}
HEADER_SIZE = 160
KEY_SIZE = 24
RES_SIZE = 8


def write_erf(out_path, paths, file_type=b"ERF "):
    """Write an ERF-family archive (ERF, HAK, MOD) containing the given files."""
    entries = []
    for path in paths:
        name = os.path.basename(path)
        resref, ext = name.lower().rsplit(".", 1)
        if len(resref) > 16:
            raise SystemExit(f"{name}: resref longer than 16 characters")
        with open(path, "rb") as f:
            entries.append((resref, RES_TYPES[ext], f.read()))

    count = len(entries)
    off_keys = HEADER_SIZE
    off_res = off_keys + count * KEY_SIZE
    off_data = off_res + count * RES_SIZE

    today = datetime.date.today()
    header = struct.pack(
        "<4s4sIIIIIIIII",
        file_type, b"V1.0",
        0, 0,                 # language count, localized string size
        count,
        off_keys,             # no localized strings: they would start here
        off_keys, off_res,
        today.year - 1900, today.timetuple().tm_yday - 1,
        0,                    # description strref (0, as Beamdog's nwn_erf writes it)
    ) + b"\0" * 116

    keys = b""
    res_list = b""
    data = b""
    for i, (resref, rtype, blob) in enumerate(entries):
        keys += struct.pack("<16sIHH", resref.encode("ascii"), i, rtype, 0)
        res_list += struct.pack("<II", off_data + len(data), len(blob))
        data += blob

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(header + keys + res_list + data)
    print(f"wrote {out_path} ({count} resources)")


def list_erf(path):
    with open(path, "rb") as f:
        blob = f.read()
    sig, ver, _lc, _ls, count, _ol, off_keys, off_res = struct.unpack_from("<4s4sIIIIII", blob, 0)
    print(f"{sig.decode()} {ver.decode()}: {count} entries")
    for i in range(count):
        resref, _rid, rtype, _ = struct.unpack_from("<16sIHH", blob, off_keys + i * KEY_SIZE)
        _offset, size = struct.unpack_from("<II", blob, off_res + i * RES_SIZE)
        print(f"  {resref.rstrip(b'\\0').decode()}.{TYPE_EXT.get(rtype, rtype)}  {size:6d} bytes")


def files(folder, ext):
    return [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.lower().endswith(ext)]


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--list":
        list_erf(sys.argv[2])
        return
    if not os.path.exists(COMPILER):
        sys.exit(f"compiler not found: {COMPILER}")

    # Start clean, so a deleted script's old .ncs is not packed.
    shutil.rmtree(NCS, ignore_errors=True)
    os.makedirs(NCS)
    result = subprocess.run([
        COMPILER, "--root", NWN_ROOT, "--userdirectory", NWN_USER,
        "--no-require-entry-point", "-y", "-d", NCS, "-c", NSS,
    ])
    if result.returncode != 0:
        sys.exit("compile failed")
    write_erf(ERF_OUT, files(NSS, ".nss") + files(NCS, ".ncs"))

    write_erf(HAK_OUT, files(SHADERS, ".shd"), b"HAK ")
    hak_dir = os.path.join(NWN_USER, "hak")
    if os.path.isdir(hak_dir):
        shutil.copy2(HAK_OUT, os.path.join(hak_dir, "nwn_mirage.hak"))
        print(f"installed {os.path.join(hak_dir, 'nwn_mirage.hak')}")
    else:
        print(f"hak folder not found ({hak_dir}); copy build/nwn_mirage.hak there yourself")


if __name__ == "__main__":
    main()
