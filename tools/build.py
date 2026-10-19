"""Build NWN-Mirage.

  py tools/build.py                     compile and pack
  py tools/build.py --nwn-root DIR      same, with the game folder given
  py tools/build.py --list FILE         print the contents of an .erf/.hak

Writes two files next to this script:
- nwn_mirage.erf: src/nss/*.nss and their compiled .ncs, for File > Import
  in the toolset.
- nwn_mirage.hak: src/shaders/*.shd; copy it to your NWN hak folder.

The script compiler needs the game's install folder (for nwscript.nss). It
is found from --nwn-root, else the NWN_ROOT environment variable, else the
Steam libraries listed in the registry.
The compiler comes from the neverwinter.nim release, unzipped into
tools/neverwinter/ (https://github.com/niv/neverwinter.nim/releases).
"""
import datetime
import os
import re
import struct
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
NSS = os.path.join(ROOT, "src", "nss")
SHADERS = os.path.join(ROOT, "src", "shaders")
ERF_OUT = os.path.join(TOOLS, "nwn_mirage.erf")
HAK_OUT = os.path.join(TOOLS, "nwn_mirage.hak")
COMPILER = os.path.join(TOOLS, "neverwinter", "nwn_script_comp.exe")
NWN_FOLDER = os.path.join("steamapps", "common", "Neverwinter Nights")

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
        name = resref.rstrip(b"\0").decode()
        print(f"  {name}.{TYPE_EXT.get(rtype, rtype)}  {size:6d} bytes")


def is_nwn_root(path):
    return bool(path) and os.path.exists(os.path.join(path, "data", "nwn_base.key"))


def steam_libraries():
    """Steam library folders, from Steam's libraryfolders.vdf."""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            steam = winreg.QueryValueEx(key, "SteamPath")[0]
    except (ImportError, OSError):
        return []
    vdf = os.path.join(steam, "steamapps", "libraryfolders.vdf")
    if not os.path.exists(vdf):
        return [steam]
    with open(vdf, encoding="utf-8", errors="replace") as f:
        paths = re.findall(r'"path"\s+"([^"]+)"', f.read())
    # The file escapes backslashes: "D:\\Games\\Steam".
    return [p.replace("\\\\", "\\") for p in paths] or [steam]


def find_nwn_root(given):
    if given:
        if not is_nwn_root(given):
            sys.exit(f"not a Neverwinter Nights folder (no data/nwn_base.key in it): {given}")
        return given
    env = os.environ.get("NWN_ROOT")
    if is_nwn_root(env):
        return env
    for library in steam_libraries():
        path = os.path.join(library, NWN_FOLDER)
        if is_nwn_root(path):
            return path
    sys.exit("Neverwinter Nights not found. Give its install folder (the one with data in it):\n"
             '  py tools/build.py --nwn-root "C:\\path\\to\\Neverwinter Nights"')


def files(folder, ext):
    return [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.lower().endswith(ext)]


def main():
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--list":
        list_erf(args[1])
        return
    given = None
    if len(args) == 2 and args[0] == "--nwn-root":
        given = args[1]
    elif args:
        sys.exit(__doc__)
    if not os.path.exists(COMPILER):
        sys.exit(f"compiler not found: {COMPILER}")
    nwn_root = find_nwn_root(given)

    # Compiled scripts go to a temporary folder, so only the two outputs are
    # left next to this script. The compiler also wants an NWN user folder;
    # the scripts need nothing from it, so an empty one will do.
    with tempfile.TemporaryDirectory() as ncs, tempfile.TemporaryDirectory() as user:
        result = subprocess.run([
            COMPILER, "--root", nwn_root, "--userdirectory", user,
            "--no-require-entry-point", "-y", "-d", ncs, "-c", NSS,
        ])
        if result.returncode != 0:
            sys.exit("compile failed")
        write_erf(ERF_OUT, files(NSS, ".nss") + files(ncs, ".ncs"))
    write_erf(HAK_OUT, files(SHADERS, ".shd"), b"HAK ")
    print("Copy nwn_mirage.hak to your NWN hak folder and import nwn_mirage.erf into your module.")


if __name__ == "__main__":
    main()
