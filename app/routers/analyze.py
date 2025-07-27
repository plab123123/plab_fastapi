from fastapi import APIRouter, HTTPException
from app.schemas.user import UserProfileRequest, UserProfile
from app.services.analysis_service import analyze_user_profile

router = APIRouter()

@router.post("/analyze")
async def analyze(user_req: UserProfileRequest):
    user = UserProfile(
        user_style=user_req.user_style,
        env=user_req.env,
        soc=user_req.soc,
        gov=user_req.gov,
        source=user_req.source,
    )

    result = await analyze_user_profile(user)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return {"result": result}
