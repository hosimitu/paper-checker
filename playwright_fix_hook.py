"""
PyInstaller ランタイムフック: playwright_fix.py
フリーズされたEXE起動時、いかなるimportより先に実行される。
Playwrightが正しいブラウザパスとドライバを参照できるよう環境変数を設定する。
"""
import os
import sys

if getattr(sys, 'frozen', False):
    # EXEが置かれているフォルダ（配布物のルート）
    base_dir = os.path.dirname(sys.executable)
    # _internal フォルダ（PyInstallerが展開するフォルダ）
    meipass = sys._MEIPASS

    # 1. ブラウザの場所を指定
    pw_browsers = os.path.join(base_dir, 'playwright_browsers')
    if os.path.exists(pw_browsers):
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = pw_browsers

    # 2. PlaywrightのNode.jsドライバの場所を指定
    #    PyInstallerが _internal/playwright/driver/ に展開する
    pw_driver_dir = os.path.join(meipass, 'playwright', 'driver')
    if os.path.exists(pw_driver_dir):
        os.environ['PLAYWRIGHT_DRIVER_PATH'] = pw_driver_dir
        # node.exe のパスを明示的に指定
        node_exe = os.path.join(pw_driver_dir, 'node.exe')
        if os.path.exists(node_exe):
            os.environ['PLAYWRIGHT_NODEJS_PATH'] = node_exe
