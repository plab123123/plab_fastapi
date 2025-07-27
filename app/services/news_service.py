from langchain_mcp_adapters.client import MultiServerMCPClient
import json
from app.core.settings import settings

class NewsQueryService:
    def __init__(self, keywords, industries, companies):
        self.queries = keywords + industries + companies
        self.summaries = []
        self.news_url = settings.news_retriever_url

    async def run(self):
        client = MultiServerMCPClient(
            {
                "news-retriever": {
                    "url": self.news_url,
                    "transport": "sse",
                }
            }
        )

        tools = await client.get_tools()
        tool = next(t for t in tools if t.name == "get_finance_news")

        for query in self.queries:
            print(f"\n [뉴스 검색]: {query}")
            try:
                result = await tool.ainvoke({"query": query})

                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError as e:
                        print(f"[뉴스 JSON 파싱 실패] (쿼리: {query}): {e}")
                        continue

                for item in result:
                    args = item.get("args", {})
                    title = args.get("title", "").strip()
                    text = args.get("text", "").strip()
                    url = args.get("url", "")

                    if title and text:
                        self.summaries.append(
                            f"제목: {title}\n 내용: {text}\n 링크: {url or '링크 없음'}\n"
                        )

            except Exception as e:
                print(f"[뉴스 mcp 연결 오류] (쿼리: {query}) → {e}")

        return "\n\n".join(self.summaries)
