import re


def clean_response(text: str) -> str:
    try:
        json_str = re.search(r"\{.*\}", text, re.DOTALL).group(0)
        return json_str.strip()
    except Exception:
        return text.strip()

def format_recommendation_output(recommendation: dict) -> str:
    user_prompt = recommendation.get("user_prompt", "사용자 요청 없음")
    summary = recommendation.get("summary_analysis", "요약 분석 없음")
    investments = recommendation.get("investment_recommendation", [])
    references = recommendation.get("references", [])

    lines = [
        f"📌 [프롬프트 요약]\n{user_prompt}",
        f"\n📌 [ESG 요약 분석]\n{summary}",
    ]

    if isinstance(investments, list):
        lines.append("\n💡 [추천 투자 기업]")
        for idx, item in enumerate(investments, 1):
            company = item.get("company_name", "기업명 없음")
            reason = item.get("reason", "추천 사유 없음")
            financial = item.get("financial_summary", {})

            lines.append(f"\n{idx}. 🏢 {company}")
            lines.append(f"   📌 추천 이유: {reason}")

            if financial:
                lines.append("   📊 최근 주요 재무 지표:")
                for key in [
                    "매출액",
                    "영업이익",
                    "영업이익률",
                    "당기순이익",
                    "부채비율",
                    "자산총계",
                    "자본총계",
                ]:
                    if key in financial:
                        lines.append(f"     - {key}: {financial[key]}")
                if "요약진단" in financial:
                    lines.append(f"     - 📈 재무 요약 진단: {financial['요약진단']}")
    else:
        lines.append(f"\n💡 [추천 투자 기업]\n{investments or '투자 추천 없음'}")

    if references:
        lines.append("\n📰 [관련 기사 목록]")
        for i, ref in enumerate(references, 1):
            title = ref.get("title", "제목 없음")
            url = ref.get("url", "링크 없음")
            lines.append(f"{i}. 📄 {title}\n   🔗 {url}")
    else:
        lines.append("\n관련 기사 없음")

    return "\n".join(lines)
