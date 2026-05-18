from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path
from typing import Any

try:
    import webview
except ImportError:
    print("Missing dependency: pywebview. Install with: uv pip install -r requirements.txt", file=sys.stderr)
    raise

from backend.config import AppConfig
from backend.constants import (
    ASPECT_RATIO_OPTIONS,
    MODEL_OPTIONS,
    QUALITY_PROFILES,
    RESOLUTION_OPTIONS,
    STYLE_OPTIONS,
    TARGET_OPTIONS,
)
from backend.modes import list_generation_modes
from backend.services.chatgpt_image_automation import ChatGptAutomationError, ChatGptImageAutomationService
from backend.services.chrome_profiles import ChromeProfileService
from backend.services.prompt_workflow import PromptWorkflow

APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
RESOURCE_ROOT = Path(getattr(sys, "_MEIPASS", APP_ROOT))
STARTUP_LOG_PATH = APP_ROOT / "Img automation App.startup.log"


def preload_frozen_pywebview_platform() -> None:
    """Make Nuitka/PyInstaller include pywebview's dynamic GUI backend modules."""
    if not (getattr(sys, "frozen", False) or "__compiled__" in globals()):
        return
    if sys.platform == "win32":
        import clr  # noqa: F401
        import clr_loader  # noqa: F401
        import pythonnet  # noqa: F401
        import webview.platforms.edgechromium  # noqa: F401
        _load_frozen_webview_win32_helper()
        import webview.platforms.winforms  # noqa: F401
    elif sys.platform == "darwin":
        import webview.platforms.cocoa  # noqa: F401


def _load_frozen_webview_win32_helper() -> None:
    if "webview.platforms.win32" in sys.modules:
        return
    helper = RESOURCE_ROOT / "webview" / "platforms" / "win32.py"
    if not helper.exists():
        return
    spec = importlib.util.spec_from_file_location("webview.platforms.win32", helper)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules["webview.platforms.win32"] = module
    spec.loader.exec_module(module)


def write_startup_log(message: str) -> None:
    try:
        STARTUP_LOG_PATH.write_text(message, encoding="utf-8")
    except Exception:
        pass


class DesktopApi:
    def __init__(self) -> None:
        self.config = AppConfig.from_env(APP_ROOT / ".env")
        self.chrome_profiles = ChromeProfileService()
        self.workflow = PromptWorkflow(self.config)
        self.chatgpt_image_automation = ChatGptImageAutomationService(self.config, APP_ROOT)

    def get_bootstrap(self) -> dict[str, Any]:
        return {
            "ok": True,
            "config": self.config.public_dict(),
            "model_options": MODEL_OPTIONS,
            "target_options": TARGET_OPTIONS,
            "quality_profiles": QUALITY_PROFILES,
            "style_options": STYLE_OPTIONS,
            "aspect_ratio_options": ASPECT_RATIO_OPTIONS,
            "resolution_options": RESOLUTION_OPTIONS,
            "generation_modes": list_generation_modes(),
            "profiles": self.chrome_profiles.list_profiles(),
        }

    def refresh_chrome_profiles(self) -> list[dict[str, Any]]:
        return self.chrome_profiles.list_profiles()

    def generate_prompt(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.workflow.generate(payload)
        except Exception as exc:
            (APP_ROOT / "Img automation App.error.log").write_text(traceback.format_exc(), encoding="utf-8")
            return {
                "ok": False,
                "error": {
                    "code": "UNEXPECTED_ERROR",
                    "message": str(exc),
                },
            }

    def test_api_key(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.workflow.test_api_key(payload.get("api_key") or self.config.pollinations_api_key)

    def open_chatgpt(self, payload: dict[str, Any]) -> dict[str, Any]:
        profile_id = payload.get("profile_id")
        profile = self.chrome_profiles.find_profile(profile_id)
        prompt_text = (payload.get("prompt_text") or "").strip()
        prompt_file = None

        if prompt_text:
            handoff_dir = APP_ROOT / ".handoff"
            handoff_dir.mkdir(exist_ok=True)
            prompt_file = handoff_dir / "chatgpt_img2_prompt.txt"
            prompt_file.write_text(prompt_text, encoding="utf-8")

        result = self.chrome_profiles.open_chatgpt(profile)
        result["prompt_file"] = str(prompt_file) if prompt_file else None
        return result

    def auto_generate_chatgpt_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return self.chatgpt_image_automation.generate_image(payload)
        except ChatGptAutomationError as exc:
            return exc.to_response()
        except Exception as exc:
            (APP_ROOT / "Img automation App.error.log").write_text(traceback.format_exc(), encoding="utf-8")
            return {
                "ok": False,
                "error": {
                    "code": "UNEXPECTED_CHATGPT_AUTOMATION_ERROR",
                    "message": str(exc),
                },
            }


def main() -> None:
    preload_frozen_pywebview_platform()
    api = DesktopApi()
    frontend = RESOURCE_ROOT / "frontend" / "index.html"
    write_startup_log(
        "\n".join(
            [
                "starting",
                f"app_root={APP_ROOT}",
                f"resource_root={RESOURCE_ROOT}",
                f"frontend={frontend}",
                f"frontend_exists={frontend.exists()}",
            ]
        )
    )
    if not frontend.exists():
        raise FileNotFoundError(f"Frontend not found: {frontend}")
    webview.create_window(
        "Img automation App",
        frontend.as_uri(),
        js_api=api,
        width=1320,
        height=860,
        min_size=(1080, 700),
        focus=True,
        on_top=False,
        background_color="#050712",
    )
    webview.start(debug=False)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log_path = APP_ROOT / "Img automation App.error.log"
        log_path.write_text(traceback.format_exc(), encoding="utf-8")
        raise
