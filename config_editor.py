import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import sys

# 多言語対応用のテキスト定義
UI_STRINGS = {
    "ja": {
        "title": "Paper-checker 設定エディタ",
        "gemini_key": "Gemini API Key:",
        "discord_url": "Discord Webhook URL:",
        "keywords": "キーワード (1行に1つ):",
        "rss_urls": "RSSフィードURL (1行に1つ):",
        "gemini_model": "Gemini モデル名:",
        "desc_model": "使用するGeminiモデルID（例: gemini-3.1-flash-lite-preview, gemini-2.0-flash, gemini-1.5-flash 等）",
        "advanced_settings": "詳細設定",
        "max_gemini": "最大 gemini 解析実行数:",
        "max_scholar": "最大論文検索試行数:",
        "desc_gemini": "1回の実行でGeminiが解析を行う論文の最大数です。",
        "desc_scholar": "Google Scholarへアクセスを試みる最大回数です。",
        "save": "保存する",
        "cancel": "キャンセル",
        "language": "表示言語 (Language):",
        "save_success": "設定を保存しました。",
        "load_error": "設定の読み込みに失敗しました:",
        "save_error": "設定の保存に失敗しました:",
        "numeric_error": "数値設定には半角数字を入力してください。",
        "key_empty_confirm": "APIキーが空欄です。保存してもよろしいですか？",
        "config_not_found": "設定ファイルが見つかりません:\n{}\n新規作成します。",
        "initial_setup_warning": "【重要】初期設定が必要です。\n設定を入力して「保存する」を押さないと、ronbun_checkerは動作しません。\n（※Gemini API Key等の入力が必要です）",
        "scholar_years": "Scholar 検索対象年数:",
        "desc_scholar_years": "Google Scholarで検索する過去何年分かの範囲（1=1年以内）",
        "captcha_timeout": "CAPTCHA解除待機(秒):",
        "desc_captcha_timeout": "手動でCAPTCHAを解除する際の最大待ち時間です。",
        "use_playwright": "Playwright(ブラウザ)使用:",
        "desc_playwright": "ONにするとブラウザを自動操作して、CAPTCHA発生時に手動解除が可能になります。",
        "wait_on_exit": "EXE終了時にキー入力待ちをする:",
        "desc_wait_on_exit": "OFFにすると処理完了後すぐに画面が閉じます。"
    },
    "en": {
        "title": "Paper-checker Config Editor",
        "gemini_key": "Gemini API Key:",
        "discord_url": "Discord Webhook URL:",
        "keywords": "Keywords (1 per line):",
        "rss_urls": "RSS Feed URLs (1 per line):",
        "gemini_model": "Gemini Model ID:",
        "desc_model": "Gemini model ID to use (e.g., gemini-3.1-flash-lite-preview, gemini-2.0-flash, gemini-1.5-flash, etc.)",
        "advanced_settings": "Advanced Settings",
        "max_gemini": "Max Gemini Analysis Executions:",
        "max_scholar": "Max Paper Search Attempts:",
        "desc_gemini": "Maximum number of papers Gemini analyzes per run.",
        "desc_scholar": "Maximum attempts to access Google Scholar per run.",
        "save": "Save",
        "cancel": "Cancel",
        "language": "Language:",
        "save_success": "Configuration saved successfully.",
        "load_error": "Failed to load configuration:",
        "save_error": "Failed to save configuration:",
        "numeric_error": "Please enter half-width numbers for numeric settings.",
        "key_empty_confirm": "API key is empty. Are you sure you want to save?",
        "config_not_found": "Configuration file not found:\n{}\nCreating a new one.",
        "initial_setup_warning": "[IMPORTANT] Initial setup is required.\nronbun_checker will not run until you enter settings and click 'Save'.\n(* Gemini API Key and other settings are required.)",
        "scholar_years": "Scholar Search Years:",
        "desc_scholar_years": "Past years range to search on Google Scholar (1=within 1 year)",
        "captcha_timeout": "CAPTCHA Timeout (sec):",
        "desc_captcha_timeout": "Maximum time to wait for manual CAPTCHA resolution.",
        "use_playwright": "Use Playwright (Browser):",
        "desc_playwright": "If ON, automates browser to allow manual CAPTCHA resolution when detected.",
        "wait_on_exit": "Wait for Enter key on exit:",
        "desc_wait_on_exit": "If OFF, the window will close immediately after finishing."
    }
}

def get_config_path():
    """設定ファイルのパスを取得する（EXE化対応）"""
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'config.json')

class ConfigEditor:
    def __init__(self, root):
        self.root = root
        self.config_path = get_config_path()
        self.config_data = {}
        self.is_initial_setup = '--initial-setup' in sys.argv
        
        # UI要素を保持する辞書（言語切り替え用）
        self.ui_labels = {}
        
        self.load_config()
        self.current_lang = self.config_data.get('language', 'ja')
        if self.current_lang not in UI_STRINGS:
            self.current_lang = 'ja'

        self.root.title(UI_STRINGS[self.current_lang]['title'])
        self.root.geometry("1100x800")
        
        # スタイルの設定（フォント一括拡大）
        self.style = ttk.Style()
        self.style.configure(".", font=("", 16))
        self.style.configure("TLabel", font=("", 16))
        self.style.configure("TButton", font=("", 16))
        self.style.configure("TEntry", font=("", 16))
        self.style.configure("TCombobox", font=("", 16))
        self.style.configure("TLabelframe.Label", font=("", 16, "bold"))

        self.create_widgets()
        self.update_ui_text()

    def create_widgets(self):
        self.scholar_years_var = tk.StringVar(value=str(self.config_data.get('scholar_search_year_range', 1)))
        self.captcha_timeout_var = tk.StringVar(value=str(self.config_data.get('manual_captcha_timeout_sec', 120)))
        init_playwright = "ON" if self.config_data.get('use_playwright', True) else "OFF"
        self.use_playwright_var = tk.StringVar(value=init_playwright)
        init_wait_exit = "ON" if self.config_data.get('wait_on_exit', True) else "OFF"
        self.wait_on_exit_var = tk.StringVar(value=init_wait_exit)

        # スクロール可能なメインエリアの作成
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, padding="20")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        # キャンバスの幅をウィンドウに合わせる
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        main_frame = self.scrollable_frame

        # Language Selection (Top)
        lang_frame = ttk.Frame(main_frame)
        lang_frame.grid(row=0, column=0, columnspan=2, sticky=tk.E, pady=(0, 10))
        
        self.ui_labels['lang_label'] = ttk.Label(lang_frame, text="")
        self.ui_labels['lang_label'].pack(side=tk.LEFT, padx=5)
        
        self.lang_var = tk.StringVar(value=self.current_lang)
        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=["ja", "en"], width=5, state="readonly")
        lang_combo.pack(side=tk.LEFT)
        lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)

        # Gemini API Key
        self.ui_labels['gemini_key'] = ttk.Label(main_frame, text="")
        self.ui_labels['gemini_key'].grid(row=1, column=0, sticky=tk.W, pady=5)
        self.gemini_key_var = tk.StringVar(value=self.config_data.get('gemini_api_key', ''))
        ttk.Entry(main_frame, textvariable=self.gemini_key_var, width=60, show="*").grid(row=1, column=1, sticky=tk.W, pady=5)

        # Gemini Model
        self.ui_labels['gemini_model'] = ttk.Label(main_frame, text="")
        self.ui_labels['gemini_model'].grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        self.gemini_model_var = tk.StringVar(value=self.config_data.get('gemini_model', 'gemini-3.1-flash-lite-preview'))
        ttk.Entry(main_frame, textvariable=self.gemini_model_var, width=60).grid(row=2, column=1, sticky=tk.W, pady=(5, 0))
        self.ui_labels['desc_model'] = ttk.Label(main_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_model'].grid(row=3, column=1, sticky=tk.W, pady=(0, 5))

        # Discord Webhook URL
        self.ui_labels['discord_url'] = ttk.Label(main_frame, text="")
        self.ui_labels['discord_url'].grid(row=4, column=0, sticky=tk.W, pady=5)
        self.discord_url_var = tk.StringVar(value=self.config_data.get('discord_webhook_url', ''))
        ttk.Entry(main_frame, textvariable=self.discord_url_var, width=65).grid(row=4, column=1, sticky=tk.W, pady=5)

        # Keywords
        self.ui_labels['keywords'] = ttk.Label(main_frame, text="")
        self.ui_labels['keywords'].grid(row=5, column=0, sticky=tk.NW, pady=5)
        self.keywords_text = scrolledtext.ScrolledText(main_frame, width=65, height=5, font=("", 14))
        self.keywords_text.grid(row=5, column=1, sticky=tk.W, pady=5)
        self.keywords_text.insert(tk.END, "\n".join(self.config_data.get('keywords', [])))

        # RSS URLs
        self.ui_labels['rss_urls'] = ttk.Label(main_frame, text="")
        self.ui_labels['rss_urls'].grid(row=6, column=0, sticky=tk.NW, pady=5)
        self.rss_text = scrolledtext.ScrolledText(main_frame, width=65, height=8, wrap=tk.NONE, font=("", 14))
        self.rss_text.grid(row=6, column=1, sticky=tk.W, pady=5)
        self.rss_text.insert(tk.END, "\n".join(self.config_data.get('rss_urls', [])))

        # Numeric Settings
        self.settings_frame = ttk.LabelFrame(main_frame, text="", padding="15")
        self.settings_frame.grid(row=7, column=0, columnspan=2, sticky=tk.EW, pady=15)

        # max_analysis_success_count
        self.ui_labels['max_gemini'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['max_gemini'].grid(row=0, column=0, sticky=tk.W)
        self.max_success_var = tk.StringVar(value=str(self.config_data.get('max_analysis_success_count', 5)))
        ttk.Entry(self.settings_frame, textvariable=self.max_success_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5)
        self.ui_labels['desc_gemini'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_gemini'].grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # max_scholar_access_attempts
        self.ui_labels['max_scholar'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['max_scholar'].grid(row=0, column=2, sticky=tk.W, padx=10)
        self.max_attempts_var = tk.StringVar(value=str(self.config_data.get('max_scholar_access_attempts', 10)))
        ttk.Entry(self.settings_frame, textvariable=self.max_attempts_var, width=10).grid(row=0, column=3, sticky=tk.W, padx=5)
        self.ui_labels['desc_scholar'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_scholar'].grid(row=1, column=2, columnspan=2, sticky=tk.W, padx=10, pady=(0, 10))

        # scholar_search_year_range
        self.ui_labels['scholar_years'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['scholar_years'].grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(self.settings_frame, textvariable=self.scholar_years_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5)
        self.ui_labels['desc_scholar_years'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_scholar_years'].grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # manual_captcha_timeout_sec
        self.ui_labels['captcha_timeout'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['captcha_timeout'].grid(row=2, column=2, sticky=tk.W, padx=10)
        ttk.Entry(self.settings_frame, textvariable=self.captcha_timeout_var, width=10).grid(row=2, column=3, sticky=tk.W, padx=5)
        self.ui_labels['desc_captcha_timeout'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_captcha_timeout'].grid(row=3, column=2, columnspan=2, sticky=tk.W, padx=10, pady=(0, 10))

        # use_playwright
        self.ui_labels['use_playwright'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['use_playwright'].grid(row=4, column=0, sticky=tk.W)
        playwright_combo = ttk.Combobox(self.settings_frame, textvariable=self.use_playwright_var, values=["ON", "OFF"], width=8, state="readonly")
        playwright_combo.grid(row=4, column=1, sticky=tk.W, padx=5)
        self.ui_labels['desc_playwright'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_playwright'].grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # wait_on_exit
        self.ui_labels['wait_on_exit'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['wait_on_exit'].grid(row=4, column=2, sticky=tk.W, padx=10)
        wait_exit_combo = ttk.Combobox(self.settings_frame, textvariable=self.wait_on_exit_var, values=["ON", "OFF"], width=8, state="readonly")
        wait_exit_combo.grid(row=4, column=3, sticky=tk.W, padx=5)
        self.ui_labels['desc_wait_on_exit'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_wait_on_exit'].grid(row=5, column=2, columnspan=2, sticky=tk.W, padx=10, pady=(0, 10))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        self.ui_labels['save_btn'] = ttk.Button(btn_frame, text="", command=self.save_config)
        self.ui_labels['save_btn'].pack(side=tk.LEFT, padx=10)
        
        self.ui_labels['cancel_btn'] = ttk.Button(btn_frame, text="", command=self.root.quit)
        self.ui_labels['cancel_btn'].pack(side=tk.LEFT, padx=10)

    def update_ui_text(self):
        """言語設定に合わせてUI文字列を更新する"""
        lang = self.current_lang
        texts = UI_STRINGS[lang]
        
        self.root.title(texts['title'])
        self.ui_labels['lang_label'].config(text=texts['language'])
        self.ui_labels['gemini_key'].config(text=texts['gemini_key'])
        self.ui_labels['discord_url'].config(text=texts['discord_url'])
        self.ui_labels['gemini_model'].config(text=texts['gemini_model'])
        self.ui_labels['desc_model'].config(text=texts['desc_model'])
        self.ui_labels['keywords'].config(text=texts['keywords'])
        self.ui_labels['rss_urls'].config(text=texts['rss_urls'])
        self.settings_frame.config(text=texts['advanced_settings'])
        self.ui_labels['max_gemini'].config(text=texts['max_gemini'])
        self.ui_labels['max_scholar'].config(text=texts['max_scholar'])
        self.ui_labels['desc_gemini'].config(text=texts['desc_gemini'])
        self.ui_labels['desc_scholar'].config(text=texts['desc_scholar'])
        self.ui_labels['scholar_years'].config(text=texts['scholar_years'])
        self.ui_labels['desc_scholar_years'].config(text=texts['desc_scholar_years'])
        self.ui_labels['captcha_timeout'].config(text=texts['captcha_timeout'])
        self.ui_labels['desc_captcha_timeout'].config(text=texts['desc_captcha_timeout'])
        self.ui_labels['use_playwright'].config(text=texts['use_playwright'])
        self.ui_labels['desc_playwright'].config(text=texts['desc_playwright'])
        self.ui_labels['wait_on_exit'].config(text=texts['wait_on_exit'])
        self.ui_labels['desc_wait_on_exit'].config(text=texts['desc_wait_on_exit'])

        self.ui_labels['save_btn'].config(text=texts['save'])
        self.ui_labels['cancel_btn'].config(text=texts['cancel'])
        
        if getattr(self, 'is_initial_setup', False) and 'initial_warning' in self.ui_labels:
            self.ui_labels['initial_warning'].config(text=texts.get('initial_setup_warning', ''))

    def on_language_change(self, event):
        self.current_lang = self.lang_var.get()
        self.update_ui_text()

    def load_config(self):
        if not os.path.exists(self.config_path):
            # messageboxを出すには一度rootを初期化する必要があるが、init中なのでここでは最小限
            self.config_data = {}
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        except Exception as e:
            # 言語が未決定なので暫定的に日本語
            print(f"Error loading config: {e}")
            self.config_data = {}

    def save_config(self):
        lang = self.current_lang
        texts = UI_STRINGS[lang]
        
        new_config = self.config_data.copy()
        new_config['language'] = self.lang_var.get()
        new_config['gemini_api_key'] = self.gemini_key_var.get().strip()
        new_config['gemini_model'] = self.gemini_model_var.get().strip()
        new_config['discord_webhook_url'] = self.discord_url_var.get().strip()
        
        keywords = self.keywords_text.get(1.0, tk.END).strip().split('\n')
        new_config['keywords'] = [k.strip() for k in keywords if k.strip()]
        
        rss_urls = self.rss_text.get(1.0, tk.END).strip().split('\n')
        new_config['rss_urls'] = [u.strip() for u in rss_urls if u.strip()]
        
        try:
            new_config['max_analysis_success_count'] = int(self.max_success_var.get())
            new_config['max_scholar_access_attempts'] = int(self.max_attempts_var.get())
            new_config['scholar_search_year_range'] = int(self.scholar_years_var.get())
            new_config['manual_captcha_timeout_sec'] = int(self.captcha_timeout_var.get())
            new_config['use_playwright'] = (self.use_playwright_var.get() == "ON")
            new_config['wait_on_exit'] = (self.wait_on_exit_var.get() == "ON")
        except ValueError:
            messagebox.showerror("Error", texts['numeric_error'])
            return

        if not new_config['gemini_api_key']:
            if not messagebox.askyesno("Confirm", texts['key_empty_confirm']):
                return

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", texts['save_success'])
            self.config_data = new_config
        except Exception as e:
            messagebox.showerror("Error", f"{texts['save_error']}\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigEditor(root)
    root.mainloop()
