import logging

import google.generativeai as genai

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Ты — ассистент продуктовой команды. Твоя задача — создавать структурированные "
    "еженедельные дайджесты на основе инсайтов от разных людей и команд. Новости можно "
    "разделять по командам, либо компоновать по смыслу. Важно: формат ответа без "
    "приветствий, сразу дайджест. Форматирование должно быть адаптировано для Slack, не md."
)


class GeminiClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-pro",
            system_instruction=SYSTEM_PROMPT,
        )

    def generate_summary(self, insights_text: str) -> str | None:
        try:
            response = self.model.generate_content(
                f"Вот инсайты за эту неделю:\n\n{insights_text}\n\nСоздай структурированный дайджест."
            )
            return response.text
        except Exception:
            logger.exception("Failed to generate summary via Gemini")
            return None
