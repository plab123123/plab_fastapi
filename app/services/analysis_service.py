import json
from app.services.ai_client import ClovaClient
from app.services.dart_service import DartService
from app.services.news_service import NewsQueryService
from app.core.utils import clean_response, format_recommendation_output

async def analyze_user_profile(user_profile):
    clova = ClovaClient()

    # 1. 유저 정보 기반 키워드/산업군/기업 추출
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

    # 2. 추출한 기업의 전자공시용 기업 코드 찾기
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
                    clova.company_codes.append(
                        {"company_name": name, "corp_code": corp_code}
                    )
                    print(f"✅ {name} → {corp_code}")
                else:
                    print(f"[기업 코드 에러] {name} 코드 없음")
            except Exception as e:
                print(f"[기업 코드 추출 에러] {name} JSON 파싱 실패:", e)

    # 3. Dart 활용하여 재무재표 찾기
    dart_service = DartService(clova.company_codes)
    dart_result = await dart_service.run()

    # 4. 뉴스 수집 및 요약
    news_service = NewsQueryService(clova.keywords, clova.industries, clova.companies)
    combined_news_text = await news_service.run()

    # 5. Dart와 뉴스를 통한 투자 판단 분석 요청
    final_recommendation_raw = clova.execute(
        {
            "messages": clova.get_recommendation_prompt(
                combined_news_text, dart_result, user_profile
            ),
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

    # 6. 결과 처리
    try:
        cleaned = clova._clean_response(final_recommendation_raw)
        recommendation = json.loads(cleaned)

        print(recommendation)

        final_output = format_recommendation_output(recommendation)
        print(final_output)
        return final_output

    except Exception as e:
        print("[최종 분석] 파싱 실패:", e)
        return {"error": str(e)}
