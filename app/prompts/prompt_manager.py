import json
from pathlib import Path
from typing import Any

import yaml

from app.schemas.user import UserProfile


class PromptManager:
    def __init__(self, base_path: Path | None = None) -> None:
        if base_path is None:
            base_path = Path(__file__).parent
        self.base_path = base_path
        self._cache: dict[str, str] = {}

    def _load_prompt(self, filename: str) -> str:
        if filename not in self._cache:
            with (self.base_path / filename).open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self._cache[filename] = data["content"]
        return self._cache[filename]

    # profile 타입으로 UserProfile 클래스를 사용할 경우 import 후 명시 가능
    def get_user_prompt(self, profile: "UserProfile") -> list[dict[str, str]]:
        content = self._load_prompt("user_prompt.yaml")
        return [
            {
                "role": "system",
                "content": content,
            },
            {
                "role": "user",
                "content": profile.to_prompt_summary(),
            },
        ]

    def get_company_code_prompt(self, company_name: str) -> list[dict[str, str]]:
        content = self._load_prompt("company_code_prompt.yaml")
        return [
            {
                "role": "system",
                "content": content,
            },
            {
                "role": "user",
                "content": f"기업명: {company_name}",
            },
        ]

    # dart_result에는 구조가 다양하므로 Any나 구체 타입으로 지정 가능
    def get_recommendation_prompt(
        self,
        combined_news_text: str,
        dart_result: Any,
        profile: "UserProfile",
    ) -> list[dict[str, str]]:
        content = self._load_prompt("recommendation_prompt.yaml")
        content_filled = content.replace("{user_prompt_summary}", profile.to_prompt_summary())
        return [
            {
                "role": "system",
                "content": content_filled,
            },
            {
                "role": "user",
                "content": (
                    f"[뉴스 요약]\n{combined_news_text}\n\n"
                    f"[기업별 재무제표 정보]\n"
                    f"{json.dumps(dart_result, ensure_ascii=False, indent=2)}"
                ),
            },
        ]
