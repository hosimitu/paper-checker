# サードパーティ・ライセンス通知 (Third-Party Notices)

本プロジェクトでは、以下のサードパーティ製ライブラリを使用しています。各ライブラリのライセンス条項に基づき、ここにライセンス情報を記載します。

## 使用ライブラリ一覧

| ライブラリ名 | ライセンス | 用途 |
| :--- | :--- | :--- |
| [scholarly](https://github.com/scholarly-python-package/scholarly) | The Unlicense | Google Scholarからの情報取得 |
| [playwright](https://github.com/microsoft/playwright-python) | Apache License 2.0 | ブラウザ自動操作・キャプチャ解除支援 |
| [playwright-stealth](https://github.com/berstend/puppeteer-extra/tree/master/packages/extract-stealth-evasions) | MIT License | Playwrightの検知回避 |
| [google-genai](https://github.com/googleapis/python-genai) | Apache License 2.0 | Gemini APIによる論文解析 |
| [requests](https://github.com/psf/requests) | Apache License 2.0 | HTTPリクエスト送信 |
| [feedparser](https://github.com/kurtmckee/feedparser) | BSD 2-Clause License | RSSフィードのパース |
| [pyinstaller](https://github.com/pyinstaller/pyinstaller) | GNU GPL v2 with exception | 実行ファイル(EXE)化 |

---

## 各ライセンスの全文（または参照先）

### Apache License 2.0
対象: `playwright`, `google-genai`, `requests`

[Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)

### MIT License
対象: `playwright-stealth`

Copyright (c) 2018 Berstend

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

### BSD 2-Clause License
対象: `feedparser`

Copyright (c) 2010-2023, Kurt McKee <contact@kurtmckee.org>
Copyright (c) 2002-2008, Mark Pilgrim

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

### The Unlicense
対象: `scholarly`

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.

(省略)

### GNU GPL v2 with Bootloader Exception
対象: `pyinstaller`

PyInstallerはGPL v2ライセンスですが、Bootloader Exceptionにより、PyInstallerを使用して作成された実行ファイル自体にはGPLの制限は適用されず、独自のライセンスで配布することが可能です。
詳細: [PyInstaller License](https://pyinstaller.org/en/stable/license.html)
