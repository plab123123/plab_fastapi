from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.settings import settings
from app.core.logging import logger

class DartService:
    def __init__(self, companies, bsns_year="2024", report_code="11014"):
        self.companies = companies
        self.bsns_year = bsns_year
        self.report_code = report_code
        self.dart_url = settings.dart_retriever_url

    async def run(self):
        client = MultiServerMCPClient(
            {
                "dart-retriever": {
                    "url": self.dart_url,
                    "transport": "sse",
                }
            }
        )

        tools = await client.get_tools()
        tool = next(t for t in tools if t.name == "get_dart_financials")

        results = []

        for c in self.companies:
            corp_code = c.get("corp_code")
            if not corp_code:
                continue

            fs_result = {}
            for sj_div in ["BS", "IS"]:
                try:
                    response = await tool.ainvoke(
                        {
                            "corp_code": corp_code,
                            "bsns_year": self.bsns_year,
                            "reprt_code": self.report_code,
                            "sj_div": sj_div,
                        }
                    )
                    fs_result[sj_div] = response
                except Exception as e:
                    logger.error(f"[Dart 응답 에러] {c['company_name']} - {sj_div} 실패: {e}")

            results.append(
                {
                    "company_name": c.get("company_name"),
                    "financial_statements": fs_result,
                }
            )
        return results
