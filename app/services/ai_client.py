import re
import json
import requests
from app.core.settings import settings

class ClovaClient:
    def __init__(self):
        self.host = settings.clova_api_host
        self.api_key = settings.clova_api_key
        self.request_id = settings.clova_request_id
        self.keywords = []
        self.industries = []
        self.companies = []
        self.company_codes = []

    def _clean_response(self, raw_response: str) -> str:
        # ```json 나 ```
        cleaned = re.sub(r"^```(?:json)?", "", raw_response.strip(), flags=re.MULTILINE)
        cleaned = cleaned.strip("`").strip()
        return cleaned


    def parse_and_store(self, result_data: str) -> None:
        try:
            cleaned = self._clean_response(result_data)
            parsed_json = json.loads(cleaned)
            self.keywords = parsed_json.get("keywords", [])
            self.industries = parsed_json.get("industries", [])
            self.companies = parsed_json.get("suggested_companies", [])
            print("🟢 키워드:", self.keywords)
            print("🟢 산업군:", self.industries)
            print("🟢 기업:", self.companies)
        except json.JSONDecodeError as e:
            print("[유저 기반 키워드 파싱 에러] JSON 파싱 실패:", e)

    def execute(self, completion_request: dict) -> str | None:
        headers = {
            "Authorization": self.api_key,
            "X-NCP-CLOVASTUDIO-REQUEST-ID": self.request_id,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream",
        }

        result_data = ""
        try:
            with requests.post(
                self.host + "/v3/chat-completions/HCX-005",
                headers=headers,
                json=completion_request,
                stream=True,
            ) as r:
                if r.status_code != 200:
                    print(f"[유저 기반 키워드 추출 실패] {r.status_code}, {r.text}")
                    return None
                for line in r.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode("utf-8")
                    if decoded.startswith('data:{"message"'):
                        try:
                            data = json.loads(decoded[5:])
                            result_data = data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
            return result_data
        except requests.exceptions.RequestException as e:
            print("[유저 기반 키워드 추출 예외]", e)
            return None

    def get_user_prompt(self, profile):
        from app.prompts.prompt_manager import PromptManager
        return PromptManager().get_user_prompt(profile)

    def get_company_code_prompt(self, company_name: str):
        from app.prompts.prompt_manager import PromptManager
        return PromptManager().get_company_code_prompt(company_name)

    def get_recommendation_prompt(self, combined_news_text, dart_result, profile):
        from app.prompts.prompt_manager import PromptManager
        return PromptManager().get_recommendation_prompt(combined_news_text, dart_result, profile)
