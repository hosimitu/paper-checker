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

*   **Delayed Evaluation Architecture**: Newly fetched papers from RSS are kept in a "Pending" state until they are indexed in Google Scholar. Once the abstract becomes available, a high-precision evaluation is performed.
*   **High-Precision Evaluation via Gemini**: Both the title and abstract are passed to Gemini, which interprets the context rather than relying on simple keyword matching to determine relevance.
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
    Create a `config.json` file and enter your settings as follows. (Note: Since it is listed in `.gitignore`, it will not be committed to Git. If it doesn't exist, create it manually.)

    ```json
    {
        "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
        "gemini_api_key": "YOUR_GEMINI_API_KEY",
        "gemini_model": "gemini-3.1-flash-lite-preview",
        "keywords": ["membrane", "CO2 separation"],
        "rss_urls": ["RSS URL for the journal"],

        "max_analysis_success_count": 5,
        "max_scholar_access_attempts": 10,
        "scholar_search_timeout_sec": 30,
        "use_playwright": true,
        "manual_captcha_timeout_sec": 120,
        "playwright_user_data_dir": ".playwright_data",
        "interval_after_success_sec": 10,
        "interval_after_notfound_sec": 20,
        "pending_item_expire_days": 30,
        "min_abstract_length": 50,
        "scholar_search_year_range": 1
    }
    ```

    Details of each item:

    | Item Name | Description | Default Value |
    |---|---|---|
    | `discord_webhook_url` | Discord Webhook URL for notifications. | - |
    | `gemini_api_key` | Google Gemini API Key. | - |
    | `gemini_model` | ID of the Gemini model to use. | `gemini-3.1-flash-lite-preview` |
    | `keywords` | List of keywords to determine relevance. | - |
    | `rss_urls` | List of RSS feed URLs to subscribe to. | - |
    | `max_analysis_success_count` | Max number of successful analyses (notifications) per execution. | `5` |
    | `max_scholar_access_attempts` | Max attempts to access Google Scholar per execution. | `10` |
    | `scholar_search_timeout_sec` | Timeout for Google Scholar search response (seconds). | `30` |
    | `use_playwright` | Enables high-precision fetching and CAPTCHA handling via Playwright. | `true` |
    | `manual_captcha_timeout_sec` | Maximum time to wait for manual CAPTCHA solving (seconds). | `120` |
    | `playwright_user_data_dir` | Directory to save browser session information. | `.playwright_data` |
    | `interval_after_success_sec` | Wait time after a successful analysis to avoid bot detection (seconds). | `10` |
    | `interval_after_notfound_sec` | Wait time when an article is not found in Scholar (seconds). | `20` |
    | `pending_item_expire_days` | Days before a pending article is auto-discarded and marked as processed. | `30` |
    | `min_abstract_length` | Minimum abstract length (characters) required to attempt analysis. | `50` |
    | `scholar_search_year_range` | Number of years to look back in Google Scholar search. | `1` |

## Usage

Execute the following command or batch file.

```bash
python main.py
```
or
```cmd
run_checker.bat
```

**Operation Recommendation:**
Use Windows "Task Scheduler" to run `run_checker.bat` periodically, such as once a day.

## File Structure

*   `main.py`: Main processing program.
*   `rss_fetcher.py`: Module to fetch article titles and links from RSS feeds.
*   `abstract_fetcher.py`: Module to fetch abstracts from Google Scholar using `scholarly`.
*   `gemini_analyzer.py`: Module to determine relevance using the Gemini API.
*   `history_manager.py`: Module to manage processed (`history.json`) and pending (`pending.json`) data.
*   `notifier.py`: Module to send notifications to a Discord Webhook.
*   `run_checker.bat`: Batch file for execution.
*   `config.json`: (User-created) Configuration file for API keys and keywords.

## Notes
*   The system is designed with Gemini API and Google Scholar rate limits in mind. If Google Scholar blocks the access, a browser window will automatically appear; please solve the CAPTCHA to resume processing.
*   Once a CAPTCHA is solved, the session information is saved in the specified directory (default: `.playwright_data`) to prevent frequent CAPTCHA requests in future runs.
*   Sensitive information and local data such as `config.json`, `history.json`, `pending.json`, and `.env` are automatically excluded from Git tracking (refer to `.gitignore`).
