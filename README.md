# Paper Checker
<table>
    <thead>
        <tr>
            <th style="text-align:center"><a href="README.md">English</a></th>
            <th style="text-align:center"><a href="README_ja.md">日本語</a></th>
        </tr>
    </thead>
</table>

A system that fetches the latest paper information from specified RSS feeds and automatically determines relevance using the Gemini API based on user-defined keywords.
Only papers deemed highly relevant are notified via a Discord Webhook.

## Key Features

*   **Delayed Evaluation Architecture**: Newly fetched papers from RSS are kept in a "Pending" state until they are indexed in Google Scholar. Once the abstract becomes available, a high-precision evaluation is performed.
*   **High-Precision Evaluation via Gemini**: Both the title and abstract are passed to Gemini, which interprets the context rather than relying on simple keyword matching to determine relevance.
*   **Duplicate Prevention**: Papers that have already been processed (either notified or deemed irrelevant) are recorded and will not be processed again.
*   **Automatic Cleanup**: Pending articles that remain unindexed in Google Scholar for a certain period (default: 30 days) are automatically discarded.

## Requirements

*   Python 3.x
*   (Recommended) Virtual environment (e.g., venv)

## Setup Instructions

1.  **Clone / Place Repository**
    Place the project in your desired directory.

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Prepare Configuration File**
    Create a `config.json` file and enter your settings as follows. (Note: Since it is listed in `.gitignore`, it will not be committed to Git. If it doesn't exist, create it manually.)

    ```json
    {
        "discord_webhook_url": "YOUR_DISCORD_WEBHOOK_URL",
        "gemini_api_key": "YOUR_GEMINI_API_KEY",
        "keywords": [
            "membrane",
            "CO2 separation"
        ],
        "rss_urls": [
            "RSS URL for the journal"
        ]
    }
    ```

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
*   The system is designed with Gemini API rate limits (RPM, RPD) in mind. If you need to process a large number of pending articles at once, adjust the `limit` value in `main.py`.
*   Sensitive information and local data such as `config.json`, `history.json`, `pending.json`, and `.env` are automatically excluded from Git tracking (refer to `.gitignore`).
