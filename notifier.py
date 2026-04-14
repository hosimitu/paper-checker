import requests
import json
from i18n import I18n

class Notifier:
    def __init__(self, webhook_url, language="ja"):
        self.webhook_url = webhook_url
        self.i18n = I18n(language)

    def notify(self, entry, reason, summarized_abstract=""):
        reason_label       = self.i18n.t("notifier.reason_label")
        abstract_label     = self.i18n.t("notifier.abstract_label")
        abstract_cont_label = self.i18n.t("notifier.abstract_cont_label")
        content_msg        = self.i18n.t("notifier.content_msg")

        # DiscordのEmbeds（埋め込み）形式を使用して、文字数制限(6000字)を回避しつつ見栄えを良くする
        embed = {
            "title": entry['title'],
            "url": entry['link'],
            "color": 3447003, # 青色
            "fields": [
                {
                    "name": reason_label,
                    "value": reason,
                    "inline": False
                }
            ]
        }

        # 要旨があれば追加
        if summarized_abstract:
            embed["fields"].append({
                "name": abstract_label,
                "value": summarized_abstract[:1024], # Fieldの文字数制限は1024字。不足ならもう一つ追加可能。
                "inline": False
            })

            # 1024文字を超える場合は後半も追加
            if len(summarized_abstract) > 1024:
                embed["fields"].append({
                    "name": abstract_cont_label,
                    "value": summarized_abstract[1024:2048],
                    "inline": False
                })

        message = {
            "content": content_msg,
            "embeds": [embed]
        }

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(message),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            print(self.i18n.t("notifier.notify_success", title=entry['title']))
        except Exception as e:
            print(self.i18n.t("notifier.notify_error", error=e))
