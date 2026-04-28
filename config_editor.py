import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import sys
from i18n import I18n

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

        # 利用可能な言語を自動検出し、見つからない場合は en にフォールバック
        available = I18n.available_languages()
        if self.current_lang not in available:
            self.current_lang = 'en' if 'en' in available else (available[0] if available else 'en')

        self.i18n = I18n(self.current_lang)

        self.root.title(self.i18n.t("config_editor.title"))
        self.root.geometry("1100x900")

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
        self.random_max_var = tk.StringVar(value=str(self.config_data.get('interval_random_max_sec', 9)))
        self.ss_api_key_var = tk.StringVar(value=self.config_data.get('semantic_scholar_api_key', ''))
        self.ss_interval_var = tk.StringVar(value=str(self.config_data.get('semantic_scholar_interval_sec', 1.5)))
        self.ss_max_var = tk.StringVar(value=str(self.config_data.get('semantic_scholar_max_attempts', 20)))

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

        # Language Selection (Top) - localesディレクトリから利用可能な言語を自動検出
        lang_frame = ttk.Frame(main_frame)
        lang_frame.grid(row=0, column=0, columnspan=2, sticky=tk.E, pady=(0, 10))

        self.ui_labels['lang_label'] = ttk.Label(lang_frame, text="")
        self.ui_labels['lang_label'].pack(side=tk.LEFT, padx=5)

        self.lang_var = tk.StringVar(value=self.current_lang)
        lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=I18n.available_languages(),
            width=5,
            state="readonly"
        )
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

        # Gemini Fallback Model
        self.ui_labels['fallback_model'] = ttk.Label(main_frame, text="")
        self.ui_labels['fallback_model'].grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        self.gemini_fallback_var = tk.StringVar(value=self.config_data.get('gemini_fallback_model', ''))
        ttk.Entry(main_frame, textvariable=self.gemini_fallback_var, width=60).grid(row=4, column=1, sticky=tk.W, pady=(5, 0))
        self.ui_labels['desc_fallback_model'] = ttk.Label(main_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_fallback_model'].grid(row=5, column=1, sticky=tk.W, pady=(0, 5))

        # Semantic Scholar API Key
        self.ui_labels['semantic_scholar_key'] = ttk.Label(main_frame, text="")
        self.ui_labels['semantic_scholar_key'].grid(row=6, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Entry(main_frame, textvariable=self.ss_api_key_var, width=60, show="*").grid(row=6, column=1, sticky=tk.W, pady=(5, 0))
        self.ui_labels['desc_semantic_scholar_key'] = ttk.Label(main_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_semantic_scholar_key'].grid(row=7, column=1, sticky=tk.W, pady=(0, 5))

        # Discord Webhook URL (shifted row)
        self.ui_labels['discord_url'] = ttk.Label(main_frame, text="")
        self.ui_labels['discord_url'].grid(row=8, column=0, sticky=tk.W, pady=5)
        self.discord_url_var = tk.StringVar(value=self.config_data.get('discord_webhook_url', ''))
        ttk.Entry(main_frame, textvariable=self.discord_url_var, width=65).grid(row=8, column=1, sticky=tk.W, pady=5)

        # Keywords (shifted row)
        self.ui_labels['keywords'] = ttk.Label(main_frame, text="")
        self.ui_labels['keywords'].grid(row=9, column=0, sticky=tk.NW, pady=5)
        self.keywords_text = scrolledtext.ScrolledText(main_frame, width=65, height=5, font=("", 14))
        self.keywords_text.grid(row=9, column=1, sticky=tk.W, pady=5)
        self.keywords_text.insert(tk.END, "\n".join(self.config_data.get('keywords', [])))

        # RSS URLs (shifted row)
        self.ui_labels['rss_urls'] = ttk.Label(main_frame, text="")
        self.ui_labels['rss_urls'].grid(row=10, column=0, sticky=tk.NW, pady=5)
        self.rss_text = scrolledtext.ScrolledText(main_frame, width=65, height=8, wrap=tk.NONE, font=("", 14))
        self.rss_text.grid(row=10, column=1, sticky=tk.W, pady=5)
        self.rss_text.insert(tk.END, "\n".join(self.config_data.get('rss_urls', [])))

        # Numeric Settings (shifted row)
        self.settings_frame = ttk.LabelFrame(main_frame, text="", padding="15")
        self.settings_frame.grid(row=11, column=0, columnspan=2, sticky=tk.EW, pady=15)

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

        # interval_random_max_sec
        self.ui_labels['random_max'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['random_max'].grid(row=6, column=0, sticky=tk.W)
        ttk.Entry(self.settings_frame, textvariable=self.random_max_var, width=10).grid(row=6, column=1, sticky=tk.W, padx=5)
        self.ui_labels['desc_random_max'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_random_max'].grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # semantic_scholar_interval_sec
        self.ui_labels['semantic_scholar_interval'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['semantic_scholar_interval'].grid(row=8, column=0, sticky=tk.W)
        ttk.Entry(self.settings_frame, textvariable=self.ss_interval_var, width=10).grid(row=8, column=1, sticky=tk.W, padx=5)
        self.ui_labels['desc_semantic_scholar_interval'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_semantic_scholar_interval'].grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # semantic_scholar_max_attempts
        self.ui_labels['semantic_scholar_max'] = ttk.Label(self.settings_frame, text="")
        self.ui_labels['semantic_scholar_max'].grid(row=8, column=2, sticky=tk.W, padx=10)
        ttk.Entry(self.settings_frame, textvariable=self.ss_max_var, width=10).grid(row=8, column=3, sticky=tk.W, padx=5)
        self.ui_labels['desc_semantic_scholar_max'] = ttk.Label(self.settings_frame, text="", font=("", 12), foreground="gray")
        self.ui_labels['desc_semantic_scholar_max'].grid(row=9, column=2, columnspan=2, sticky=tk.W, padx=10, pady=(0, 10))

        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=12, column=0, columnspan=2, pady=20)

        self.ui_labels['save_btn'] = ttk.Button(btn_frame, text="", command=self.save_config)
        self.ui_labels['save_btn'].pack(side=tk.LEFT, padx=10)

        self.ui_labels['cancel_btn'] = ttk.Button(btn_frame, text="", command=self.root.quit)
        self.ui_labels['cancel_btn'].pack(side=tk.LEFT, padx=10)

    def update_ui_text(self):
        """言語設定に合わせてUI文字列を更新する"""
        t = self.i18n.t

        self.root.title(t("config_editor.title"))
        self.ui_labels['lang_label'].config(text=t("config_editor.language"))
        self.ui_labels['gemini_key'].config(text=t("config_editor.gemini_key"))
        self.ui_labels['discord_url'].config(text=t("config_editor.discord_url"))
        self.ui_labels['gemini_model'].config(text=t("config_editor.gemini_model"))
        self.ui_labels['desc_model'].config(text=t("config_editor.desc_model"))
        self.ui_labels['fallback_model'].config(text=t("config_editor.fallback_model"))
        self.ui_labels['desc_fallback_model'].config(text=t("config_editor.desc_fallback_model"))
        self.ui_labels['keywords'].config(text=t("config_editor.keywords"))
        self.ui_labels['rss_urls'].config(text=t("config_editor.rss_urls"))
        self.settings_frame.config(text=t("config_editor.advanced_settings"))
        self.ui_labels['max_gemini'].config(text=t("config_editor.max_gemini"))
        self.ui_labels['max_scholar'].config(text=t("config_editor.max_scholar"))
        self.ui_labels['desc_gemini'].config(text=t("config_editor.desc_gemini"))
        self.ui_labels['desc_scholar'].config(text=t("config_editor.desc_scholar"))
        self.ui_labels['scholar_years'].config(text=t("config_editor.scholar_years"))
        self.ui_labels['desc_scholar_years'].config(text=t("config_editor.desc_scholar_years"))
        self.ui_labels['captcha_timeout'].config(text=t("config_editor.captcha_timeout"))
        self.ui_labels['desc_captcha_timeout'].config(text=t("config_editor.desc_captcha_timeout"))
        self.ui_labels['use_playwright'].config(text=t("config_editor.use_playwright"))
        self.ui_labels['desc_playwright'].config(text=t("config_editor.desc_playwright"))
        self.ui_labels['wait_on_exit'].config(text=t("config_editor.wait_on_exit"))
        self.ui_labels['desc_wait_on_exit'].config(text=t("config_editor.desc_wait_on_exit"))
        self.ui_labels['random_max'].config(text=t("config_editor.random_max"))
        self.ui_labels['desc_random_max'].config(text=t("config_editor.desc_random_max"))
        self.ui_labels['semantic_scholar_key'].config(text=t("config_editor.semantic_scholar_key"))
        self.ui_labels['desc_semantic_scholar_key'].config(text=t("config_editor.desc_semantic_scholar_key"))
        self.ui_labels['semantic_scholar_interval'].config(text=t("config_editor.semantic_scholar_interval"))
        self.ui_labels['desc_semantic_scholar_interval'].config(text=t("config_editor.desc_semantic_scholar_interval"))
        self.ui_labels['semantic_scholar_max'].config(text=t("config_editor.semantic_scholar_max"))
        self.ui_labels['desc_semantic_scholar_max'].config(text=t("config_editor.desc_semantic_scholar_max"))
        self.ui_labels['save_btn'].config(text=t("config_editor.save"))
        self.ui_labels['cancel_btn'].config(text=t("config_editor.cancel"))

        if getattr(self, 'is_initial_setup', False) and 'initial_warning' in self.ui_labels:
            self.ui_labels['initial_warning'].config(text=t("config_editor.initial_setup_warning"))

    def on_language_change(self, event):
        """言語ドロップダウン変更時にi18nを再ロードしてUIを更新する"""
        self.current_lang = self.lang_var.get()
        self.i18n.set_language(self.current_lang)
        self.update_ui_text()

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.config_data = {}
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            self.config_data = {}

    def save_config(self):
        t = self.i18n.t

        new_config = self.config_data.copy()
        new_config['language'] = self.lang_var.get()
        new_config['gemini_api_key'] = self.gemini_key_var.get().strip()
        new_config['gemini_model'] = self.gemini_model_var.get().strip()
        new_config['gemini_fallback_model'] = self.gemini_fallback_var.get().strip()
        new_config['discord_webhook_url'] = self.discord_url_var.get().strip()

        keywords = self.keywords_text.get(1.0, tk.END).strip().split('\n')
        new_config['keywords'] = [k.strip() for k in keywords if k.strip()]

        rss_urls = self.rss_text.get(1.0, tk.END).strip().split('\n')
        new_config['rss_urls'] = [u.strip() for u in rss_urls if u.strip()]

        try:
            new_config['max_analysis_success_count']  = int(self.max_success_var.get())
            new_config['max_scholar_access_attempts'] = int(self.max_attempts_var.get())
            new_config['scholar_search_year_range']   = int(self.scholar_years_var.get())
            new_config['manual_captcha_timeout_sec']  = int(self.captcha_timeout_var.get())
            new_config['interval_random_max_sec']     = int(self.random_max_var.get())
            new_config['semantic_scholar_api_key']    = self.ss_api_key_var.get().strip()
            new_config['semantic_scholar_interval_sec'] = float(self.ss_interval_var.get())
            new_config['semantic_scholar_max_attempts'] = int(self.ss_max_var.get())
            new_config['use_playwright'] = (self.use_playwright_var.get() == "ON")
            new_config['wait_on_exit']   = (self.wait_on_exit_var.get() == "ON")
        except ValueError:
            messagebox.showerror("Error", t("config_editor.numeric_error"))
            return

        if not new_config['gemini_api_key']:
            if not messagebox.askyesno("Confirm", t("config_editor.key_empty_confirm")):
                return

        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Success", t("config_editor.save_success"))
            self.config_data = new_config
        except Exception as e:
            messagebox.showerror("Error", f"{t('config_editor.save_error')}\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigEditor(root)
    root.mainloop()
