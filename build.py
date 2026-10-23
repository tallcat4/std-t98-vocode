"""Build the pinned ambe2-c library and run its reference vectors with GCC/Clang."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REVISION = "bfa9c26b203117d65c68303a87968fd7e89855d9"
SOURCES = (
    "b25_dsp_a.c b25_dsp_b.c b25_decode_c.c b25_decode_d.c b25_tables.c "
    "b25_golay.c blip25.c mbelib_compat.c ambeplus.c ambeplus_tables.c "
    "ambeplus_fec.c ambeplus4000_tables.c ambeplus_layer2.c"
).split()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", help="GCC or Clang executable")
    args = parser.parse_args()
    source = ROOT / "ambe2-c-source"
    if not (source / "decoder/include/blip25.h").is_file():
        raise RuntimeError("Fetch ambe2-c-source first; see README for the pinned revision")
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if revision != REVISION:
        raise RuntimeError(f"Expected ambe2-c {REVISION}, found {revision}")
    dirty = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"], text=True)
    if dirty.strip():
        raise RuntimeError("ambe2-c-source has modified tracked files; use the unmodified pinned source")
    compiler = args.compiler or shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not compiler and Path("C:/Strawberry/c/bin/gcc.exe").is_file():
        compiler = "C:/Strawberry/c/bin/gcc.exe"
    if not compiler:
        raise RuntimeError("Install GCC/Clang; on Windows use 64-bit MinGW or --compiler PATH")
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    decoder = source / "decoder"
    flags = [compiler, "-std=c99", "-O2", "-I" + str(decoder / "include"), "-I" + str(decoder / "src")]
    sources = [str(decoder / "src" / f) for f in SOURCES]
    if sys.platform == "win32":
        name, shared, link, suffix = "ambe2.dll", ["-shared"], ["-static"], ".exe"
    elif sys.platform == "darwin":
        name, shared, link, suffix = "libambe2.dylib", ["-dynamiclib", "-fPIC"], ["-lm"], ""
    else:
        name, shared, link, suffix = "libambe2.so", ["-shared", "-fPIC"], ["-lm"], ""
    def run(command):
        subprocess.run(command, check=True)
    run(flags + shared + sources + link + ["-o", str(build / name)])
    # Native oracle for adapter/bit-order tests and upstream fixed-point vectors.
    for target, entry in (("ambe2wav", "examples/ambe2wav.c"), ("ambe2-tests", "tests/run_tests.c")):
        run(flags + [str(decoder / entry)] + sources + link + ["-o", str(build / (target + suffix))])
    run([str(build / ("ambe2-tests" + suffix)), str(decoder / "tests/vectors")])
    print(f"Ready: {build / name} (ambe2-c {revision})")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
