import re
import json
import requests
from app.core.settings import settings
from app.core.logging import logger

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
        """
        GPT 응답 텍스트에서 JSON 블록을 안전하게 추출합니다.
        - 마크다운 코드블럭 제거
        - 응답 내 중간에 JSON 블록이 포함되어 있어도 추출
        - 파싱 가능한 JSON 형식이 아니면 빈 문자열 반환
        """
        try:
            # 1. 백틱 및 마크다운 코드블럭 제거
            text = raw_response.strip().strip("`")
            text = re.sub(r"^```(?:json|JSON)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)

            # 2. JSON 블록만 추출 (가장 큰 {} 블록을 감지)
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                logger.warning(f"[JSON 블록 없음] 원문: {text[:100]}...")
                return ""

            json_block = match.group(0).strip()

            # 3. 대충 봤을 때도 JSON 아닌 경우 (속도 위해 최소한 체크)
            if not json_block.startswith("{") or not json_block.endswith("}"):
                logger.warning(f"[JSON 형식 아님] 추정 결과: {json_block[:100]}...")
                return ""

            return json_block
        except Exception as e:
            logger.error(f"[_clean_response 오류] {e}")
            return ""


    def parse_and_store(self, result_data: str) -> None:
        logger.info(f"[Raw result data] {result_data}")

        cleaned = self._clean_response(result_data)
        logger.info(f"[Cleaned result data] {cleaned}")

        if not cleaned:
            logger.warning("[유저 기반 키워드 파싱] 정제된 응답이 비어 있습니다. 기본값으로 처리합니다.")
            # 비어 있어도 빈 리스트로 초기화 (굳이 다시 설정하지 않아도 되지만 명시적으로 표현)
            self.keywords = []
            self.industries = []
            self.companies = []
            return

        try:
            parsed_json = json.loads(cleaned)
            self.keywords = parsed_json.get("keywords", [])
            self.industries = parsed_json.get("industries", [])
            self.companies = parsed_json.get("suggested_companies", [])
            logger.info(f"🟢 키워드: {self.keywords}")
            logger.info(f"🟢 산업군: {self.industries}")
            logger.info(f"🟢 기업: {self.companies}")
        except json.JSONDecodeError as e:
            logger.warning(f"[유저 기반 키워드 파싱 경고] JSON 파싱 실패 → 빈 값 처리: {e}")
            self.keywords = []
            self.industries = []
            self.companies = []


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
                    logger.error(f"[유저 기반 키워드 추출 실패] {r.status_code}, {r.text}")
                    return None
                for line in r.iter_lines():
                    if not line:
                        continue
                    decoded = line.decode("utf-8")
                    if decoded.startswith('data:{"message"'):
                        try:
                            data = json.loads(decoded[5:])
                            content = data["message"]["content"]
                            if content:
                                result_data = content.strip()
                        except json.JSONDecodeError:
                            continue
            return result_data
        except requests.exceptions.RequestException as e:
            logger.error(f"[유저 기반 키워드 추출 예외] {e}")
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
