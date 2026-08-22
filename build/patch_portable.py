from pathlib import Path
import sys

# Temporary helper used only while GitHub Actions produces the portable archives.
# This branch-only marker exists to trigger the observable PR build.
bundle = Path(sys.argv[1])
path = bundle / "app" / "src" / "collector" / "direct_webcast_process.mjs"
text = path.read_text(encoding="utf-8")

old_args = '''    const args = [\n      scriptPath,\n      this.username,'''
new_args = '''    const bundledCollector = process.env.DIRECT_COLLECTOR_BIN?.trim();\n    const args = [\n      ...(bundledCollector ? [] : [scriptPath]),\n      this.username,'''
old_spawn = '''    const child = spawn(this.pythonBin, args, {'''
new_spawn = '''    const child = spawn(bundledCollector || this.pythonBin, args, {'''

if old_args not in text:
    raise SystemExit("Không tìm thấy đoạn args cần patch")
if old_spawn not in text:
    raise SystemExit("Không tìm thấy đoạn spawn cần patch")

text = text.replace(old_args, new_args, 1).replace(old_spawn, new_spawn, 1)
path.write_text(text, encoding="utf-8")
print(f"Patched portable collector launcher: {path}")
