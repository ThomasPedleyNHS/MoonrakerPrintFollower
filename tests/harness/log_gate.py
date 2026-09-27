"""The same plugin-log verdict for native and container Cura journeys."""
from pathlib import Path
import re
import sys


def plugin_log_noise(text):
    qml_names = {path.name for path in
                 (Path(__file__).resolve().parents[2] / "plugins").glob("*.qml")}
    noisy = re.compile(r"\b(?:WARNING|ERROR|TypeError|ReferenceError)\b|(?i:(?:polish|binding) loop)")
    owned = re.compile(r"MoonrakerPrintFollower|\b(?:Moonraker|Plate|Gpu|Follower|Monitor)\w*\.qml")
    return [(number, line) for number, line in enumerate(text.splitlines(), 1)
            if noisy.search(line) and (owned.search(line)
                or any(name in line for name in qml_names))]


def check_logs(paths):
    failed = False
    paths = list(paths)
    if not paths:
        print("ui_test: no Cura logs available for validation", file=sys.stderr)
        return 1
    for path in paths:
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"ui_test: cannot read Cura log {path}: {exc}", file=sys.stderr)
            failed = True
            continue
        for line, message in plugin_log_noise(text):
            print(f"ui_test: CURA LOG NOISE: {path}:{line}: {message}", file=sys.stderr)
            failed = True
    if not failed:
        print("ui_test: cura.log scan clean")
    return int(failed)


if __name__ == "__main__":
    sys.exit(check_logs(sys.argv[1:]))
