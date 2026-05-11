from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import Any


class ChromeProfileService:
    def __init__(self) -> None:
        self.system = platform.system().lower()

    def list_profiles(self) -> list[dict[str, Any]]:
        profiles: list[dict[str, Any]] = []
        for browser in self._browser_roots():
            local_state = browser["user_data_dir"] / "Local State"
            names = self._read_profile_names(local_state)
            if not self._path_exists(browser["user_data_dir"]):
                continue

            try:
                children = sorted(browser["user_data_dir"].iterdir(), key=lambda item: item.name.lower())
            except OSError:
                continue

            for child in children:
                if not child.is_dir() or not self._looks_like_profile(child):
                    continue
                profile_id = f"{browser['name']}::{child.name}"
                display_name = names.get(child.name) or ("Default" if child.name == "Default" else child.name)
                profiles.append(
                    {
                        "id": profile_id,
                        "browser": browser["name"],
                        "name": display_name,
                        "directory": child.name,
                        "path": str(child),
                        "user_data_dir": str(browser["user_data_dir"]),
                        "executable": str(browser["executable"]) if browser["executable"] else "",
                    }
                )
        return profiles

    def find_profile(self, profile_id: str | None) -> dict[str, Any] | None:
        if not profile_id:
            return None
        return next((profile for profile in self.list_profiles() if profile["id"] == profile_id), None)

    def open_chatgpt(self, profile: dict[str, Any] | None) -> dict[str, Any]:
        url = "https://chatgpt.com/"
        executable = Path(profile["executable"]) if profile and profile.get("executable") else self._default_chrome_executable()
        if not executable or not executable.exists():
            return {
                "ok": False,
                "error": "Không tìm thấy Chrome/Edge executable để mở ChatGPT.",
            }

        args = [str(executable)]
        if profile:
            args.extend([f"--user-data-dir={profile['user_data_dir']}", f"--profile-directory={profile['directory']}"])
        args.append(url)
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"ok": True, "url": url, "profile": profile}

    def _browser_roots(self) -> list[dict[str, Any]]:
        home = Path.home()
        roots: list[dict[str, Any]] = []

        if self.system == "windows":
            local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
            program_files = [Path(os.environ.get("PROGRAMFILES", "C:/Program Files")), Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))]
            roots.extend(
                [
                    {
                        "name": "Chrome",
                        "user_data_dir": local / "Google" / "Chrome" / "User Data",
                        "executable": self._first_existing([p / "Google" / "Chrome" / "Application" / "chrome.exe" for p in program_files]),
                    },
                    {
                        "name": "Edge",
                        "user_data_dir": local / "Microsoft" / "Edge" / "User Data",
                        "executable": self._first_existing([p / "Microsoft" / "Edge" / "Application" / "msedge.exe" for p in program_files]),
                    },
                ]
            )
        elif self.system == "darwin":
            roots.extend(
                [
                    {
                        "name": "Chrome",
                        "user_data_dir": home / "Library" / "Application Support" / "Google" / "Chrome",
                        "executable": Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
                    },
                    {
                        "name": "Edge",
                        "user_data_dir": home / "Library" / "Application Support" / "Microsoft Edge",
                        "executable": Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
                    },
                ]
            )
        else:
            roots.extend(
                [
                    {"name": "Chrome", "user_data_dir": home / ".config" / "google-chrome", "executable": self._which("google-chrome")},
                    {"name": "Chromium", "user_data_dir": home / ".config" / "chromium", "executable": self._which("chromium")},
                ]
            )
        return roots

    def _default_chrome_executable(self) -> Path | None:
        for root in self._browser_roots():
            executable = root.get("executable")
            if executable and Path(executable).exists():
                return Path(executable)
        return None

    @staticmethod
    def _first_existing(paths: list[Path]) -> Path | None:
        return next((path for path in paths if path.exists()), None)

    @staticmethod
    def _which(command: str) -> Path | None:
        for folder in os.environ.get("PATH", "").split(os.pathsep):
            candidate = Path(folder) / command
            if candidate.exists():
                return candidate
        return None

    @staticmethod
    def _looks_like_profile(path: Path) -> bool:
        return path.name == "Default" or path.name.startswith("Profile ") or ChromeProfileService._path_exists(path / "Preferences")

    @staticmethod
    def _read_profile_names(local_state: Path) -> dict[str, str]:
        if not ChromeProfileService._path_exists(local_state):
            return {}
        try:
            data = json.loads(local_state.read_text(encoding="utf-8"))
            info = data.get("profile", {}).get("info_cache", {})
            return {key: value.get("name", key) for key, value in info.items() if isinstance(value, dict)}
        except Exception:
            return {}

    @staticmethod
    def _path_exists(path: Path) -> bool:
        try:
            return path.exists()
        except OSError:
            return False
