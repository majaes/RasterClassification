"""Build the installable QGIS zip (releases/RasterClassification-<version>.zip).

Usage (from the repository root):
    python dev/build_zip.py

Every file tracked by git (or new and not ignored) is packed under the folder
RasterClassification/, except dev tooling, releases and hidden files.
Then the plugin's Python files are compiled to catch syntax errors.
"""
import os
import py_compile
import re
import subprocess
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_DIR = "RasterClassification"
EXCLUDED = re.compile(r"^(dev|releases|debug|docs)/|(^|/)\.[^/]*$|^(Makefile|DEVELOPMENT\.md)$")


def version():
    with open(os.path.join(ROOT, "metadata.txt"), encoding="utf-8") as f:
        return re.search(r"^version=(\S+)", f.read(), re.M).group(1)


def files():
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True, check=True)
    return [p for p in out.stdout.splitlines() if p and not EXCLUDED.search(p)
            and os.path.exists(os.path.join(ROOT, p))]


def main():
    names = files()
    for n in names:
        if n.endswith(".py"):
            py_compile.compile(os.path.join(ROOT, n), cfile=os.path.join(tempfile.gettempdir(), "scp_chk.pyc"), doraise=True)
    os.makedirs(os.path.join(ROOT, "releases"), exist_ok=True)
    path = os.path.join(ROOT, "releases", "%s-%s.zip" % (PLUGIN_DIR, version()))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(os.path.join(ROOT, n), "%s/%s" % (PLUGIN_DIR, n))
    print("%d files -> %s (%.1f MB)" % (len(names), path, os.path.getsize(path) / 1e6))


if __name__ == "__main__":
    main()
