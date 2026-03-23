from google import genai
from google.genai import types
import json

class GeminiRateLimitError(Exception):
    """Gemini APIのレート制限（429等）を検知した際の例外"""
    pass

class GeminiAnalyzer:
    def __init__(self, api_key, keywords, model_id="gemini-3.1-flash-lite-preview", language="ja"):
        self.client = genai.Client(api_key=api_key)
        self.keywords = keywords
        self.model_id = model_id
        self.language = language

    def analyze_entry(self, entry):
        if self.language == "en":
            prompt = f"""
You are an expert in determining the relevance of research papers.
Read the title and abstract of the following paper and determine if it is relevant to the user's interests (keywords).

【User's Interests (Keywords)】
{', '.join(self.keywords)}

【Paper Information】
Title: {entry['title']}
Abstract: {entry['summary']}

【Decision Rules】
1. Determine "is_relevant" as true only if the title or abstract is directly or strongly related to the user's interests.
2. Return the decision results in JSON format.
    - "is_relevant": true or false
    - "reason": A concise reason for the decision in English (if relevant, include which keyword it relates to)
    - "translated_abstract": An accurate English summary of the paper's abstract (must be provided regardless of relevance)

【Output Format】
Output JSON only.
"""
            abstract_key = "translated_abstract"
            default_reason = "No reason provided"
        else: # ja
            prompt = f"""
あなたは論文の関連性を判定する専門家です。
以下の論文のタイトルと要旨を読み、ユーザーの関心事（キーワード）に関連があるかどうかを判定してください。

【ユーザーの関心事（キーワード）】
{', '.join(self.keywords)}

【論文情報】
タイトル: {entry['title']}
要旨: {entry['summary']}

【判定ルール】
1. タイトルまたは要旨から、ユーザーの関心事に直接的または強く関連する場合のみ「関連あり」と判定してください。
2. 判定結果はJSON形式で返してください。
    - "is_relevant": true または false
    - "reason": 簡潔な日本語の判定理由（関連がある場合はどのキーワードに関連するかを含める）
    - "japanese_abstract": 論文の要旨の正確な日本語訳（関連性の有無に関わらず、必ず記述してください）

【出力形式】
JSONのみを出力してください。
"""
            abstract_key = "japanese_abstract"
            default_reason = "判定理由なし"
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
            return (
                result.get("is_relevant", False), 
                result.get("reason", default_reason),
                result.get(abstract_key, "")
            )
        except Exception as e:
            error_msg = str(e)
            # レート制限 (429 Too Many Requests や Resource Exhausted) をチェック
            if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                print(f"CRITICAL: Gemini API Rate Limit exceeded! ({error_msg})")
                raise GeminiRateLimitError(f"Gemini quota exceeded: {error_msg}")
                
            print(f"Gemini解析中にエラーが発生しました: {e}")
            return False, f"解析エラー: {e}", ""
