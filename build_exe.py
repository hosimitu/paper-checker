import os
import subprocess
import shutil
import sys

def run_command(command, description):
    print(f"\n--- {description} ---")
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)

def build():
    cwd = os.getcwd()
    dist_dir = os.path.join(cwd, "dist")
    build_dir = os.path.join(cwd, "build")
    
    # クリーンアップ
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

    # 1. 依存ライブラリのインストール (PyInstaller含む)
    run_command("pip install pyinstaller playwright-stealth scholarly google-genai feedparser requests", "依存ライブラリをインストール中")

    # 2. Playwright ブラウザのダウンロード
    print("\n--- Playwrightブラウザ(Chromium)をダウンロード中 ---")
    # ローカルフォルダにブラウザをインストールし、配布物に含められるようにする
    pw_browsers_path = os.path.join(cwd, 'playwright_browsers')
    if os.path.exists(pw_browsers_path):
        shutil.rmtree(pw_browsers_path)
    os.makedirs(pw_browsers_path)
    
    env = os.environ.copy()
    env['PLAYWRIGHT_BROWSERS_PATH'] = pw_browsers_path
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True, env=env)
    except Exception as e:
        print(f"Playwrightのインストールに失敗しました: {e}")
        sys.exit(1)

    # 3. PyInstaller ビルド (main.py)
    # --onedir 形式でビルドし、playwright_browsers を含める
    run_command(
        f"pyinstaller --noconfirm --onedir --name ronbun_checker "
        f"--add-data \"playwright_browsers;playwright_browsers\" "
        f"--runtime-hook playwright_fix_hook.py "
        f"--collect-all playwright "
        f"--collect-all playwright_stealth "
        f"--console main.py",
        "本体(main.py)をビルド中"
    )

    # 4. PyInstaller ビルド (config_editor.py)
    # 設定エディタは、本体フォルダに移動しやすくするため --onefile (単一ファイル) でビルドします
    run_command(
        f"pyinstaller --noconfirm --onefile --name config_editor "
        f"--noconsole config_editor.py",
        "設定エディタ(config_editor.py)をビルド中"
    )

    # 5. 成果物の整理
    print("\n--- 配布用フォルダの整理中 ---")
    final_output = os.path.join(dist_dir, "ronbun_checker")
    # --onefile の場合、exeは dist 直下に生成される
    editor_exe = os.path.join(dist_dir, "config_editor.exe")
    
    if os.path.exists(editor_exe):
        shutil.copy(editor_exe, final_output)
        print(f"config_editor.exe を {final_output} にコピーしました。")

    # playwright_browsers が _internal の中に生成されている場合は、ルートに移動する（hook や .bat の想定に合わせる）
    internal_pw_browsers = os.path.join(final_output, "_internal", "playwright_browsers")
    root_pw_browsers = os.path.join(final_output, "playwright_browsers")
    if os.path.exists(internal_pw_browsers) and not os.path.exists(root_pw_browsers):
        shutil.move(internal_pw_browsers, root_pw_browsers)
        print("playwright_browsers を配布フォルダのルートに移動しました。")

    print("\n" + "="*60)
    print("ビルドが完了しました！")
    print(f"配布用フォルダ: {final_output}")
    print("  - ronbun_checker.exe: 論文チェック本体（直接ダブルクリックで起動可能）")
    print("  - config_editor.exe: 設定ツール")
    print("このフォルダをZIPにして配布してください。")
    print("="*60)

if __name__ == "__main__":
    build()
