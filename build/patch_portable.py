from pathlib import Path
import shutil
import sys

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

app_path = bundle / "app" / "a.mjs"
app_text = app_path.read_text(encoding="utf-8")
old_host = 'const apiHost = process.env.API_HOST?.trim() || "127.0.0.1";'
new_host = 'const apiHost = process.env.API_HOST?.trim() || "0.0.0.0";'
if old_host not in app_text:
    raise SystemExit("Không tìm thấy API_HOST mặc định cần patch")
app_path.write_text(app_text.replace(old_host, new_host, 1), encoding="utf-8")
print(f"Patched portable LAN API host: {app_path}")

firewall_helper = Path("source") / "allow-lan.bat"
if sys.platform == "win32" and firewall_helper.exists():
    shutil.copy2(firewall_helper, bundle / "allow-lan.bat")
    print(f"Copied Windows LAN firewall helper: {bundle / 'allow-lan.bat'}")
