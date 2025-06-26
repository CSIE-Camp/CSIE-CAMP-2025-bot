#!/usr/bin/env python3
"""
專案健康檢查腳本

檢查專案的依賴、配置和基本功能是否正常
"""

import sys
import json
import importlib.util
from pathlib import Path
from typing import List, Tuple


# 顏色輸出
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_status(message: str, status: str, color: str = Colors.GREEN):
    """打印狀態訊息"""
    print(f"{message:<50} [{color}{status}{Colors.ENDC}]")


def check_python_version() -> bool:
    """檢查 Python 版本"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_status("Python 版本", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_status(
            "Python 版本",
            f"{version.major}.{version.minor}.{version.micro} (需要 3.8+)",
            Colors.RED,
        )
        return False


def check_dependencies() -> bool:
    """檢查依賴套件"""
    required_packages = [
        "discord",
        "aiohttp",
        "requests",
        "dotenv",
        "pydantic",
        "google.genai",
    ]

    all_installed = True

    for package in required_packages:
        try:
            if package == "google.genai":
                import google.genai  # noqa: F401

                print_status(f"套件: {package}", "已安裝")
            else:
                __import__(package)
                print_status(f"套件: {package}", "已安裝")
        except ImportError:
            print_status(f"套件: {package}", "未安裝", Colors.RED)
            all_installed = False

    return all_installed


def check_env_file() -> Tuple[bool, List[str]]:
    """檢查環境變數檔案"""
    env_path = Path(".env")
    missing_vars = []

    if not env_path.exists():
        print_status(".env 檔案", "不存在", Colors.RED)
        return False, []

    print_status(".env 檔案", "存在")

    # 讀取環境變數
    required_vars = ["DISCORD_TOKEN", "GEMINI_API_KEY"]

    optional_vars = [
        "MYGO_CHANNEL_ID",
        "REWARD_CHANNEL_ID",
        "EASTER_EGG_CHANNEL_ID",
        "SCOREBOARD_CHANNEL_ID",
    ]

    with open(env_path, "r", encoding="utf-8") as f:
        env_content = f.read()

    # 檢查必要變數
    for var in required_vars:
        if (
            f"{var}=" in env_content
            and len(env_content.split(f"{var}=")[1].split("\n")[0].strip()) > 0
        ):
            print_status(f"環境變數: {var}", "已設定")
        else:
            print_status(f"環境變數: {var}", "未設定", Colors.RED)
            missing_vars.append(var)

    # 檢查可選變數
    for var in optional_vars:
        if (
            f"{var}=" in env_content
            and len(env_content.split(f"{var}=")[1].split("\n")[0].strip()) > 0
        ):
            print_status(f"環境變數: {var}", "已設定")
        else:
            print_status(f"環境變數: {var}", "未設定", Colors.YELLOW)

    return len(missing_vars) == 0, missing_vars


def check_data_directory() -> bool:
    """檢查資料目錄"""
    data_dir = Path("data")

    if not data_dir.exists():
        print_status("data 目錄", "不存在", Colors.YELLOW)
        print(f"  {Colors.YELLOW}建議: 建立 data 目錄{Colors.ENDC}")
        return False

    print_status("data 目錄", "存在")

    # 檢查資料檔案
    data_files = [
        "acg_quotes.json",
        "achievement.json",
        "flags.json",
        "mygo.json",
        "schedule.json",
    ]

    for file_name in data_files:
        file_path = data_dir / file_name
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json.load(f)
                print_status(f"  資料檔: {file_name}", "有效")
            except json.JSONDecodeError:
                print_status(f"  資料檔: {file_name}", "格式錯誤", Colors.RED)
        else:
            print_status(f"  資料檔: {file_name}", "不存在", Colors.YELLOW)

    return True


def check_source_structure() -> bool:
    """檢查原始碼結構"""
    required_dirs = ["src", "src/cogs", "src/utils"]

    required_files = [
        "src/__init__.py",
        "src/camp_bot.py",
        "src/config.py",
        "src/constants.py",
    ]

    all_present = True

    # 檢查目錄
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print_status(f"目錄: {dir_path}", "存在")
        else:
            print_status(f"目錄: {dir_path}", "不存在", Colors.RED)
            all_present = False

    # 檢查檔案
    for file_path in required_files:
        if Path(file_path).exists():
            print_status(f"檔案: {file_path}", "存在")
        else:
            print_status(f"檔案: {file_path}", "不存在", Colors.RED)
            all_present = False

    return all_present


def check_cogs() -> bool:
    """檢查 Cog 模組"""
    cogs_dir = Path("src/cogs")

    if not cogs_dir.exists():
        print_status("Cogs 目錄", "不存在", Colors.RED)
        return False

    cog_files = list(cogs_dir.glob("*.py"))
    cog_files = [f for f in cog_files if not f.name.startswith("__")]

    print_status("Cogs 目錄", f"找到 {len(cog_files)} 個模組")

    for cog_file in cog_files:
        try:
            spec = importlib.util.spec_from_file_location(cog_file.stem, cog_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "setup"):
                print_status(f"  Cog: {cog_file.stem}", "有效")
            else:
                print_status(
                    f"  Cog: {cog_file.stem}", "缺少 setup 函數", Colors.YELLOW
                )
        except Exception:
            print_status(f"  Cog: {cog_file.stem}", "載入錯誤", Colors.RED)

    return len(cog_files) > 0


def main():
    """主函數"""
    print(
        f"\n{Colors.BOLD}{Colors.BLUE}=== NTNU CSIE Camp Bot 健康檢查 ==={Colors.ENDC}\n"
    )

    checks = [
        ("Python 環境", check_python_version),
        ("依賴套件", check_dependencies),
        ("環境變數", lambda: check_env_file()[0]),
        ("資料目錄", check_data_directory),
        ("原始碼結構", check_source_structure),
        ("Cog 模組", check_cogs),
    ]

    passed = 0
    total = len(checks)

    for check_name, check_func in checks:
        print(f"\n{Colors.BOLD}=== {check_name} ==={Colors.ENDC}")
        if check_func():
            passed += 1

    # 總結
    print(f"\n{Colors.BOLD}=== 檢查總結 ==={Colors.ENDC}")

    if passed == total:
        print_status("整體狀態", f"通過 ({passed}/{total})")
        print(f"\n{Colors.GREEN}✅ 專案健康狀況良好！可以啟動機器人。{Colors.ENDC}")
    else:
        print_status("整體狀態", f"部分失敗 ({passed}/{total})", Colors.YELLOW)
        print(f"\n{Colors.YELLOW}⚠️  請修復上述問題後再啟動機器人。{Colors.ENDC}")

    # 提供建議
    print(f"\n{Colors.BOLD}=== 啟動建議 ==={Colors.ENDC}")
    print("1. 確保所有必要環境變數已設定")
    print("2. 運行: python -m src.camp_bot")
    print("3. 檢查控制台輸出是否有錯誤")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
