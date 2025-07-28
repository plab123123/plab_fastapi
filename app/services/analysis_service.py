import json
from app.services.ai_client import ClovaClient
from app.services.dart_service import DartService
from app.services.news_service import NewsQueryService
from app.core.utils import clean_response, format_recommendation_output
from app.core.logging import logger

async def analyze_user_profile(user_profile):
    clova = ClovaClient()

    result = clova.execute(
        {
            "messages": clova.get_user_prompt(user_profile),
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 512,
            "temperature": 0.5,
            "repetitionPenalty": 1.1,
            "stop": [],
            "includeAiFilters": True,
            "seed": 0,
        }
    )
    clova.parse_and_store(result)

    clova.company_codes = []
    for name in clova.companies:
        prompt = clova.get_company_code_prompt(name)

        company_code_result = clova.execute(
            {
                "messages": prompt,
                "topP": 0.8,
                "topK": 0,
                "maxTokens": 512,
                "temperature": 0.5,
                "repetitionPenalty": 1.1,
                "stop": [],
                "includeAiFilters": True,
                "seed": 0,
            }
        )

        if company_code_result:
            try:
                cleaned = clova._clean_response(company_code_result)
                parsed = json.loads(cleaned)
                corp_code = parsed.get("corp_code")
                if corp_code:
                    clova.company_codes.append({"company_name": name, "corp_code": corp_code})
                    logger.info(f"✅ {name} → {corp_code}")
                else:
                    logger.error(f"[기업 코드 에러] {name} 코드 없음")
            except Exception as e:
                logger.error(f"[기업 코드 추출 에러] {name} JSON 파싱 실패: {e}")

    dart_service = DartService(clova.company_codes)
    dart_result = await dart_service.run()

    news_service = NewsQueryService(clova.keywords, clova.industries, clova.companies)
    combined_news_text = await news_service.run()

    final_recommendation_raw = clova.execute(
        {
            "messages": clova.get_recommendation_prompt(combined_news_text, dart_result, user_profile),
            "topP": 0.8,
            "topK": 0,
            "maxTokens": 1024,
            "temperature": 0.5,
            "repetitionPenalty": 1.1,
            "stop": [],
            "includeAiFilters": True,
            "seed": 0,
        }
    )

    try:
        cleaned = clova._clean_response(final_recommendation_raw)
        recommendation = json.loads(cleaned)
    except Exception as e:
        logger.error(f"[최종 분석] JSON 파싱 실패: {e}")
        recommendation = {}

    final_output = format_recommendation_output(recommendation)
    return final_output or {"message": "조건에 부합하는 적합한 기업이 없습니다."}