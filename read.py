#!/usr/bin/env python3
"""
每日励志思考桌面应用（带缓存，可打包为 exe）

功能：
 - 启动时显示“今日励志语录”（从 ZenQuotes API 获取 /today）
 - 支持手动刷新（随机一条）/ 复制到剪贴板 / 关闭
 - 本地缓存（~/.daily_quote_cache.json），同一天内重复打开显示同一条
 - 失败时回退到本地内置备用语录

打包提示见 README.md（使用 PyInstaller）。
"""
from __future__ import annotations
import json
import os
import time
import traceback
from typing import Optional, Dict, Any
import requests
import tkinter as tk
from tkinter import ttk, messagebox

APP_NAME = "DailyInspire"
CACHE_FILE = os.path.expanduser("~/.daily_quote_cache.json")
API_TODAY = "https://zenquotes.io/api/today"
API_RANDOM = "https://zenquotes.io/api/random"
DEFAULT_TIMEOUT = 6.0

BACK_QUOTES = [
    {"q": "不要等待机会，而要创造机会。", "a": "未知"},
    {"q": "你今天所做的努力，会在未来悄悄改变你的生活。", "a": "未知"},
    {"q": "昨天的你比今天的你更懒惰，别让它继续。", "a": "未知"},
]


def _today_date_str() -> str:
    return time.strftime("%Y-%m-%d")


def load_cache() -> Dict[str, Any]:
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_cached_today() -> Optional[Dict[str, str]]:
    cache = load_cache()
    entry = cache.get("today")
    if not entry:
        return None
    if entry.get("date") == _today_date_str() and entry.get("quote"):
        return entry["quote"]
    return None


def set_cached_today(quote_obj: Dict[str, str]) -> None:
    cache = load_cache()
    cache["today"] = {"date": _today_date_str(), "quote": quote_obj}
    save_cache(cache)


def fetch_from_api(url: str, timeout: float = DEFAULT_TIMEOUT) -> Optional[Dict[str, str]]:
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": f"{APP_NAME}/1.0"})
        r.raise_for_status()
        data = r.json()
        # ZenQuotes returns list of objects: [{"q": "...", "a":"...","h":"<p>...</p>"}]
        if isinstance(data, list) and data:
            q = data[0].get("q") or ""
            a = data[0].get("a") or ""
            return {"q": q.strip(), "a": a.strip()}
    except Exception:
        return None
    return None


def get_today_quote(use_cache: bool = True) -> Dict[str, str]:
    # 1) cached today
    if use_cache:
        cached = get_cached_today()
        if cached:
            return cached

    # 2) try API /today
    q = fetch_from_api(API_TODAY)
    if q:
        set_cached_today(q)
        return q

    # 3) fallback: try random
    q = fetch_from_api(API_RANDOM)
    if q:
        set_cached_today(q)
        return q

    # 4) last resort: fallback local list (pick by date index)
    idx = int(time.time() // (24 * 3600)) % len(BACK_QUOTES)
    back = BACK_QUOTES[idx]
    set_cached_today(back)
    return back


def get_random_quote() -> Dict[str, str]:
    q = fetch_from_api(API_RANDOM)
    if q:
        # don't necessarily cache random as "today"; user expects refresh, but we can cache as 'last_random'
        cache = load_cache()
        cache["last_random"] = {"ts": int(time.time()), "quote": q}
        save_cache(cache)
        return q
    # fallback local random
    import random
    return random.choice(BACK_QUOTES)


class QuoteApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("每日励志思考")
        # make small dialog-like window, centered
        self.root.resizable(False, False)
        self._setup_widgets()
        # show today's quote on start
        self.show_today()

    def _setup_widgets(self):
        pad = 12
        self.frame = ttk.Frame(self.root, padding=pad)
        self.frame.grid(row=0, column=0, sticky="nsew")
        # Quote text (wrapped)
        self.quote_var = tk.StringVar(value="")
        self.quote_label = tk.Label(self.frame, textvariable=self.quote_var,
                                    wraplength=420, justify="center",
                                    font=("Helvetica", 12), padx=10, pady=10)
        self.quote_label.grid(row=0, column=0, columnspan=3, sticky="nsew")
        # Author
        self.author_var = tk.StringVar(value="")
        self.author_label = tk.Label(self.frame, textvariable=self.author_var,
                                     font=("Helvetica", 10, "italic"))  # 不用 tuple
        self.author_label.grid(row=1, column=0, columnspan=3, pady=(0, 8))

        # Buttons: New, Copy, Close
        self.btn_new = ttk.Button(self.frame, text="刷新（随机）", command=self.on_new)
        self.btn_new.grid(row=2, column=0, padx=6)
        self.btn_copy = ttk.Button(self.frame, text="复制", command=self.on_copy)
        self.btn_copy.grid(row=2, column=1, padx=6)
        self.btn_close = ttk.Button(self.frame, text="关闭", command=self.root.quit)
        self.btn_close.grid(row=2, column=2, padx=6)

        # status label
        self.status_var = tk.StringVar(value="")
        self.status_label = tk.Label(self.frame, textvariable=self.status_var, font=("Helvetica", 8))
        self.status_label.grid(row=3, column=0, columnspan=3, pady=(8,0))

        # set geometry
        self._center_window(480, 200)

    def _center_window(self, w: int, h: int):
        self.root.update_idletasks()
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        x = (ws // 2) - (w // 2)
        y = (hs // 2) - (h // 2) - 40
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def show_today(self):
        self._set_status("加载今日语录…")
        try:
            q = get_today_quote(use_cache=True)
            self._display_quote(q)
            self._set_status("显示今天的励志语录。点击“刷新（随机）”获取新一句。")
        except Exception as e:
            self._set_status("获取失败，显示备用语录。")
            self._display_quote({"q": "无法获取在线语录。", "a": ""})
            print("Error in show_today:", e)
            traceback.print_exc()

    def on_new(self):
        self._set_status("获取随机语录…")
        self.root.update_idletasks()
        try:
            q = get_random_quote()
            # update UI and also update today's cache if you want:
            # set_cached_today(q)
            self._display_quote(q)
            self._set_status("已刷新（随机）。")
        except Exception as e:
            self._set_status("刷新失败。")
            messagebox.showerror("错误", f"无法获取新的语录：{e}")

    def on_copy(self):
        text = f"“{self.quote_var.get()}” — {self.author_var.get()}"
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self._set_status("已复制到剪贴板。")
        except Exception:
            self._set_status("复制失败。")

    def _display_quote(self, qobj: Dict[str, str]):
        q = qobj.get("q", "")
        a = qobj.get("a", "")
        if not a:
            a = "未知"
        self.quote_var.set(q)
        self.author_var.set(f"— {a}")

    def _set_status(self, text: str):
        self.status_var.set(text)


def main():
    root = tk.Tk()
    # optionally use themed style
    try:
        style = ttk.Style()
        style.theme_use("clam")
    except Exception:
        pass
    app = QuoteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()