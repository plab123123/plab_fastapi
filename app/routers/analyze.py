from fastapi import APIRouter, HTTPException
from app.schemas.user import UserProfileRequest, UserProfile
from app.services.analysis_service import analyze_user_profile
from app.core.logging import logger

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

    try:
        result = await analyze_user_profile(user)
    except Exception as e:
        logger.error(f"/analyze 핸들러 예외 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    if isinstance(result, dict) and "error" in result:
        logger.error(f"/analyze 내부 오류: {result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])
    
    return {"result": result}
