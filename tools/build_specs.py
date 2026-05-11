"""Render the 4 PyInstaller specs from pyinstaller.spec.template.

Usage:
    python tools/build_specs.py
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "pyinstaller.spec.template"

VARIANTS = [
    {
        "file": "Img automation App.spec",
        "APP_NAME": "Img automation App",
        "DEBUG": "False",
        "CONSOLE": "False",
        "ONEFILE": True,
    },
    {
        "file": "Img automation App Debug.spec",
        "APP_NAME": "Img automation App Debug",
        "DEBUG": "True",
        "CONSOLE": "True",
        "ONEFILE": True,
    },
    {
        "file": "Img automation App Portable.spec",
        "APP_NAME": "Img automation App Portable",
        "DEBUG": "False",
        "CONSOLE": "False",
        "ONEFILE": False,
    },
    {
        "file": "Img automation App Debug Portable.spec",
        "APP_NAME": "Img automation App Debug Portable",
        "DEBUG": "True",
        "CONSOLE": "True",
        "ONEFILE": False,
    },
]


def render(variant: dict) -> str:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    if variant["ONEFILE"]:
        exe_extra = "a.binaries,\n    a.zipfiles,\n    a.datas,"
        collect = ""
    else:
        exe_extra = ""
        collect = (
            "coll = COLLECT(\n"
            "    exe,\n    a.binaries,\n    a.zipfiles,\n    a.datas,\n"
            "    strip=False, upx=True, upx_exclude=[],\n"
            f"    name='{variant['APP_NAME']}',\n"
            ")\n"
        )

    output = template
    for key in ("APP_NAME", "DEBUG", "CONSOLE"):
        output = output.replace("{{" + key + "}}", variant[key])
    output = output.replace("{{EXTRA_HIDDENIMPORTS}}", "")
    output = output.replace("{{EXE_EXTRA_ARGS}}", exe_extra)
    output = output.replace("{{COLLECT_BLOCK}}", collect)
    return output


def main() -> None:
    for variant in VARIANTS:
        target = ROOT / variant["file"]
        target.write_text(render(variant), encoding="utf-8")
        print(f"rendered {variant['file']}")


if __name__ == "__main__":
    main()
