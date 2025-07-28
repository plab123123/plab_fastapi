import re
import json
from app.core.logging import logger


def clean_response(text: str) -> str:
    """
    응답 텍스트에서 JSON 객체 부분만 추출하고, 공백 제거 후 반환
    """
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            cleaned = match.group(0).strip()
            logger.debug(f"clean_response: JSON 추출 성공 → {cleaned[:100]}...")
            return cleaned
        else:
            logger.warning("clean_response: JSON 구조 감지 실패. 원본 텍스트 반환")
            return text.strip()
    except Exception as e:
        logger.error(f"clean_response 예외 발생: {e}")
        return text.strip()


def format_recommendation_output(recommendation: dict) -> str:
    """
    AI 분석 결과 recommendation dict를 사람이 읽기 좋은 문자열로 변환합니다.
    """
    try:
        user_prompt = recommendation.get("user_prompt") or "사용자 요청 없음"
        summary = recommendation.get("summary_analysis") or "요약 분석 없음"
        investments = recommendation.get("investment_recommendation") or []
        references = recommendation.get("references") or []

        lines = [
            f"📌 [프롬프트 요약]\n{user_prompt}",
            f"\n📌 [ESG 요약 분석]\n{summary}",
        ]

        # 추천 투자 기업
        if isinstance(investments, list) and investments:
            lines.append("\n💡 [추천 투자 기업]")
            for idx, item in enumerate(investments, 1):
                company = item.get("company_name") or "기업명 없음"
                reason = item.get("reason") or "추천 사유 없음"
                financial = item.get("financial_summary") or {}

                lines.append(f"\n{idx}. 🏢 {company}")
                lines.append(f"   📌 추천 이유: {reason}")

                if isinstance(financial, dict) and financial:
                    lines.append("   📊 최근 주요 재무 지표:")
                    for key in [
                        "매출액", "영업이익", "영업이익률",
                        "당기순이익", "부채비율", "자산총계", "자본총계"
                    ]:
                        val = financial.get(key)
                        if val is not None and not isinstance(val, (list, dict)):
                            lines.append(f"     - {key}: {val}")

                    summary_val = financial.get("요약진단")
                    if summary_val:
                        lines.append(f"     - 📈 재무 요약 진단: {summary_val}")
        else:
            lines.append(f"\n💡 [추천 투자 기업]\n{investments or '투자 추천 없음'}")

        # 참고 기사
        if isinstance(references, list) and references:
            lines.append("\n📰 [관련 기사 목록]")
            for i, ref in enumerate(references, 1):
                title = ref.get("title") or "제목 없음"
                url = ref.get("url") or "링크 없음"
                lines.append(f"{i}. 📄 {title}\n   🔗 {url}")
        else:
            lines.append("\n관련 기사 없음")

        formatted_output = "\n".join(lines)
        logger.debug("format_recommendation_output: 출력 결과 생성 완료")
        return formatted_output

    except Exception as e:
        logger.error(f"format_recommendation_output 에러: {e}")
        return "출력 포매팅 중 오류가 발생했습니다."
