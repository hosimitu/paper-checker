from google import genai
from google.genai import types
import json
import time
from i18n import I18n

class GeminiRateLimitError(Exception):
    """Gemini APIのレート制限（429等）を検知した際の例外"""
    pass

class GeminiUnavailableError(Exception):
    """Gemini APIの503エラー（一時不可）を検知した際の例外"""
    pass

class GeminiNotFoundError(Exception):
    """Gemini APIの404エラー（モデルなし等）を検知した際の例外"""
    pass

class GeminiAnalysisError(Exception):
    """Gemini APIの解析中（パース等）に発生した一般的な例外"""
    pass

class GeminiAnalyzer:
    def __init__(self, api_key, keywords, model_id="gemini-3.1-flash-lite-preview", language="ja"):
        self.client = genai.Client(api_key=api_key)
        self.keywords = keywords
        self.model_id = model_id
        self.i18n = I18n(language)

    def analyze_entry(self, entry):
        # 推論は常に英語で行い、出力言語のみlanguage設定で切り替える
        output_instruction = self.i18n.t("gemini.output_instruction")
        abstract_key       = self.i18n.t("gemini.abstract_key")
        default_reason     = self.i18n.t("gemini.default_reason")

        prompt = f"""
You are an expert academic reviewer specializing in evaluating the relevance of research papers.
Read the title and abstract of the following paper and determine whether it is relevant to the user's research interests.

[User's Research Interests (Keywords)]
{', '.join(self.keywords)}

[Paper Information]
Title: {entry['title']}
Abstract: {entry['summary']}

[Evaluation Rules]
1. Mark "is_relevant" as true ONLY if the paper is directly or strongly related to the user's interests.
   - Consider not just keyword matching, but the underlying logic, novelty, and research context.
   - A paper using similar methods but addressing an unrelated domain should be marked false.
2. Return the result in JSON format with the following fields:
   - "is_relevant": true or false
   {output_instruction}

[Output Format]
Output JSON only. Do not include any explanation outside the JSON.
"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                result = json.loads(response.text)

                # gemma-4-31b-it 等のモデルがリスト形式 [...] で返してくる場合への対応
                if isinstance(result, list):
                    result = result[0] if result else {}

                if not isinstance(result, dict):
                    result = {}

                return (
                    result.get("is_relevant", False),
                    result.get("reason", default_reason),
                    result.get(abstract_key, "")
                )
            except Exception as e:
                error_msg = str(e)
                # 503エラー (UNAVAILABLE) かどうかチェック
                is_unavailable = "503" in error_msg or "UNAVAILABLE" in error_msg

                if is_unavailable and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"Gemini API 503 UNAVAILABLE! {wait_time}秒後にリトライします... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(wait_time)
                    continue

                # レート制限 (429等) をチェック
                if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                    print(f"CRITICAL: Gemini API Rate Limit exceeded! ({error_msg})")
                    raise GeminiRateLimitError(f"Gemini quota exceeded: {error_msg}")

                # 404 (モデルが見つからない等) をチェック
                if "404" in error_msg or "not found" in error_msg.lower():
                    raise GeminiNotFoundError(self.i18n.t("gemini.error_not_found", error=error_msg))

                # 503がリトライ後も続く場合
                if is_unavailable:
                    raise GeminiUnavailableError(f"Gemini remains unavailable after {max_retries} attempts: {error_msg}")

                print(self.i18n.t("gemini.error_analyze", error=e))
                # デバッグ用にレスポンスの生データを出力する（JSON形式が想定と異なる場合の調査用）
                try:
                    if 'response' in locals() and hasattr(response, 'text'):
                        print(f"--- Debug: Raw Gemini Response ---\n{response.text}\n----------------------------------")
                except:
                    pass
                raise GeminiAnalysisError(str(e))
