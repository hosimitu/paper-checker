# Paper Checker (論文チェッカー)
<table>
    <thead>
        <tr>
            <th style="text-align:center">English</th>
            <th style="text-align:center"><a href="README_ja.md">日本語</a></th>
        </tr>
    </thead>
</table>

A system that fetches the latest paper information from specified RSS feeds and automatically determines relevance using the Gemini API based on user-defined keywords.
Only papers deemed highly relevant are notified via a Discord Webhook.

## Key Features

*   **GUI Configuration Editor**: Use `config_editor.py` (or the built executable) to easily set up API keys, keywords, and other settings via an intuitive interface without manual JSON editing.
*   **Executable (EXE) Build Support**: Bundled `build_exe.py` script allows you to create standalone executables for distribution to users without a Python environment.
*   **Delayed Evaluation Architecture**: Newly fetched papers from RSS are kept in a "Pending" state until they are indexed in Google Scholar. Once the abstract becomes available, a high-precision evaluation is performed.
*   **High-Precision Evaluation via Gemini**: Both the title and abstract are passed to Gemini, which interprets the context rather than relying on simple keyword matching to determine relevance.
*   **Semantic Scholar API Integration**: Added the ability to pre-fetch abstracts using the Semantic Scholar API for faster and more stable data collection without CAPTCHA interruptions.
*   **Fail-safe and Automatic Intervention**: Includes logic to avoid Google Scholar bot detection. If blocked, it automatically displays a browser for the user to manually solve the CAPTCHA and continue.
*   **Session Persistence**: Saves and reuses the solved CAPTCHA state to project directory, ensuring fewer interruptions and smoother operation.
*   **Duplicate Prevention**: Papers that have already been processed (either notified or deemed irrelevant) are recorded and will not be processed again.

## Requirements

*   Python 3.x
*   (Recommended) Virtual environment (e.g., venv)

## Setup Instructions

1.  **Clone / Place Repository**
    Place the project in your desired directory.

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

3.  **Prepare Configuration File**
    Prepare the `config.json` file. The easiest way is to use the dedicated GUI tool:

    ```bash
    python config_editor.py
    ```
    Follow the instructions on the screen to enter your API key, Webhook URL, keywords, etc., then click "Save" to automatically generate `config.json`.

    (If you prefer manual creation, refer to the template below.)

    ```json
    {
        "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
        "gemini_api_key": "YOUR_GEMINI_API_KEY",
        "gemini_model": "gemini-3.1-flash-lite-preview",
        "gemini_fallback_model": "gemma-4-26b-a4b-it",
        "keywords": ["membrane", "CO2 separation"],
        "rss_urls": ["RSS URL for the journal"],

        "max_analysis_success_count": 5,
        "max_scholar_access_attempts": 10,
        "scholar_search_timeout_sec": 30,
        "use_playwright": true,
        "manual_captcha_timeout_sec": 120,
        "playwright_user_data_dir": ".playwright_data",
        "wait_on_exit": true,
        "interval_after_success_sec": 10,
        "interval_after_notfound_sec": 20,
        "interval_random_max_sec": 9,
        "pending_item_expire_days": 30,
        "min_abstract_length": 50,
        "scholar_search_year_range": 1,
        "semantic_scholar_api_key": "YOUR_SEMANTIC_SCHOLAR_API_KEY",
        "semantic_scholar_interval_sec": 1.5,
        "semantic_scholar_max_attempts": 20
    }
    ```

    Details of each item:

    | Item Name | Description | Default Value |
    |---|---|---|
    | `discord_webhook_url` | Discord Webhook URL for notifications. | - |
    | `gemini_api_key` | Google Gemini API Key. | - |
    | `gemini_model` | ID of the Gemini model to use. | `gemini-3.1-flash-lite-preview` |
    | `gemini_fallback_model` | Fallback model ID to use when Gemini API limit is exceeded or an error occurs. | - |
    | `keywords` | List of keywords to determine relevance. | - |
    | `rss_urls` | List of RSS feed URLs to subscribe to. | - |
    | `max_analysis_success_count` | Max number of successful analyses (notifications) per execution. | `5` |
    | `max_scholar_access_attempts` | Max attempts to access Google Scholar per execution. | `10` |
    | `scholar_search_timeout_sec` | Timeout for Google Scholar search response (seconds). | `30` |
    | `use_playwright` | Enables high-precision fetching and CAPTCHA handling via Playwright. | `true` |
    | `manual_captcha_timeout_sec` | Maximum time to wait for manual CAPTCHA solving (seconds). | `120` |
    | `playwright_user_data_dir` | Directory to save browser session information. | `.playwright_data` |
    | `wait_on_exit` | Whether to wait before closing the console window after execution. | `true` |
    | `interval_after_success_sec` | Wait time after a successful analysis to avoid bot detection (seconds). | `10` |
    | `interval_after_notfound_sec` | Wait time when an article is not found in Scholar (seconds). | `20` |
    | `interval_random_max_sec` | Maximum random seconds to add to the wait time. | `9` |
    | `pending_item_expire_days` | Days before a pending article is auto-discarded and marked as processed. | `30` |
    | `min_abstract_length` | Minimum abstract length (characters) required to attempt analysis. | `50` |
    | `scholar_search_year_range` | Number of years to look back in Google Scholar search. | `1` |
    | `semantic_scholar_api_key` | Semantic Scholar API Key (works without it but with stricter limits). | - |
    | `semantic_scholar_interval_sec` | Request interval for Semantic Scholar API in seconds (min 1.0). | `1.5` |
    | `semantic_scholar_max_attempts` | Max attempts to access Semantic Scholar per execution. | `20` |

## Usage

**Configuration**
To create or update your settings, launch the config editor:
```bash
python config_editor.py
```

**Run Paper Check**
Execute the following command or batch file.

```bash
python main.py
```
or
```cmd
run_checker.bat
```

**Abstract Prefetching**
To prefetch and supplement abstracts for pending articles using the Semantic Scholar API, run the following. This significantly reduces CAPTCHA occurrences in Google Scholar.

```bash
python semantic_prefetch.py
```
or
```cmd
run_prefetch.bat
```

**Build Executable (EXE)**
To create standalone executables for distribution (useful for Windows users without Python):
```bash
python build_exe.py
```
After building, the executables will be generated in the `dist/ronbun_checker/` folder.

**Operation Recommendation:**
Use Windows "Task Scheduler" to run `run_checker.bat` periodically, such as once a day.

## File Structure

*   `main.py`: Main processing program.
*   `config_editor.py`: GUI tool to easily create and edit the configuration file (`config.json`).
*   `build_exe.py`: Automation script to build standalone executables (EXE) for the project.
*   `rss_fetcher.py`: Module to fetch article titles and links from RSS feeds.
*   `abstract_fetcher.py`: Module to fetch abstracts from Google Scholar.
*   `semantic_scholar_fetcher.py`: Module to fetch abstracts using Semantic Scholar API.
*   `semantic_prefetch.py`: Script to batch-fetch abstracts for pending articles.
*   `gemini_analyzer.py`: Module to determine relevance using the Gemini API and generate summaries.
*   `history_manager.py`: Module to manage processing history and pending data (SQLite).
*   `notifier.py`: Module to send rich notifications to a Discord Webhook.
*   `run_checker.bat`: Batch file for execution.
*   `run_prefetch.bat`: Batch file for prefetching abstracts.
*   `config.json`: (User-created/Auto-generated) Configuration file for API keys and keywords.
*   `history.db`: (Auto-generated) SQLite database to store processed and pending data.

## Notes
*   The system is designed with Gemini API and Google Scholar rate limits in mind. If Google Scholar blocks the access, a browser window will automatically appear; please solve the CAPTCHA to resume processing.
*   Once a CAPTCHA is solved, the session information is saved in the specified directory (default: `.playwright_data`) to prevent frequent CAPTCHA requests in future runs.
*   Sensitive information and local data such as `config.json`, `history.db`, and `.env` are automatically excluded from Git tracking (refer to `.gitignore`).
*   If existing `history.json` or `pending.json` files are present, they will be automatically migrated to `history.db` on the first run, and the original files will be renamed to `.bak` as a backup.
