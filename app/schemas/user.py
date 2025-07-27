from pydantic import BaseModel

class UserProfileRequest(BaseModel):
    user_style: str
    env: float
    soc: float
    gov: float
    source: str

class UserProfile:
    def __init__(self, user_style: str, env: float, soc: float, gov: float, source: str):
        self.user_style = user_style
        self.env = env
        self.soc = soc
        self.gov = gov
        self.source = source

    def to_prompt_summary(self) -> str:
        return (
            f"나는 {self.user_style} 투자자이며 ESG 비중은 환경 {self.env}%, "
            f"사회 {self.soc}%, 지배구조 {self.gov}%야. {self.source} 기반으로 국내 기업 추천해줘."
        )

    def to_dict(self):
        return {
            "user_style": self.user_style,
            "env": self.env,
            "soc": self.soc,
            "gov": self.gov,
            "source": self.source,
        }
