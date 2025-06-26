#!/usr/bin/env python3
"""
機器人啟動腳本

提供便捷的機器人啟動方式，包含預檢查和錯誤處理
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_health_check() -> bool:
    """運行健康檢查"""
    print("🔍 正在進行啟動前檢查...\n")

    try:
        result = subprocess.run(
            [sys.executable, "health_check.py"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            print("✅ 健康檢查通過！")
            return True
        else:
            print("❌ 健康檢查失敗！")
            print(result.stdout)
            return False

    except FileNotFoundError:
        print("⚠️ 健康檢查腳本不存在，跳過檢查")
        return True
    except (subprocess.SubprocessError, OSError):
        print("⚠️ 健康檢查時發生錯誤，跳過檢查")
        return True


def start_bot():
    """啟動機器人"""
    print("🚀 正在啟動機器人...")

    try:
        # 使用模組方式啟動機器人
        subprocess.run([sys.executable, "-m", "src.camp_bot"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 機器人已手動停止")
    except subprocess.CalledProcessError as e:
        print(f"❌ 機器人啟動失敗：{e}")
        sys.exit(1)
    except (OSError, RuntimeError) as e:
        print(f"❌ 啟動時發生錯誤：{e}")
        sys.exit(1)


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="NTNU CSIE Camp Bot 啟動器")
    parser.add_argument(
        "--skip-check", action="store_true", help="跳過健康檢查直接啟動"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="只進行健康檢查，不啟動機器人"
    )

    args = parser.parse_args()

    print("🤖 NTNU CSIE Camp 2025 Discord Bot")
    print("=" * 40)

    # 檢查當前目錄
    if not Path("src/camp_bot.py").exists():
        print("❌ 錯誤：請在專案根目錄執行此腳本")
        sys.exit(1)

    # 健康檢查
    if not args.skip_check:
        if not run_health_check():
            if not args.check_only:
                response = input("\n⚠️ 健康檢查失敗，是否仍要啟動機器人？(y/N): ")
                if response.lower() != "y":
                    print("❌ 啟動已取消")
                    sys.exit(1)

        if args.check_only:
            print("✅ 健康檢查完成")
            return

    # 啟動機器人
    start_bot()


if __name__ == "__main__":
    main()
