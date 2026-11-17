from fastapi import APIRouter, Depends, HTTPException, status
from ai_service import AIOutputError, AIServiceError, get_verdict
from redaction import redact
from database import get_connection
from dependencies import get_current_user
from models import CheckCreate, CheckDetail, CheckSummary, FeedbackUpdate
from rate_limit import enforce_ai_limit

router = APIRouter(prefix="/checks", tags=["checks"])

def _get_check_detail(conn, check_id: int, user_id: int):
    check = conn.execute(
        "SELECT id, message_text, risk_level, summary, next_steps, feedback, created_at "
        "FROM checks WHERE id = %s AND user_id = %s",
        (check_id, user_id),
    ).fetchone()
    if check is None:
        raise HTTPException(status_code=404, detail="Check not found")
    check["red_flags"] = conn.execute(
        "SELECT type, explanation FROM red_flags WHERE check_id = %s ORDER BY id",
        (check_id,),
    ).fetchall()
    return check


@router.post("", response_model=CheckDetail, status_code=status.HTTP_201_CREATED)
def create_check(payload: CheckCreate, user=Depends(get_current_user)):
    
    try:
        enforce_ai_limit(user["id"])
        verdict = get_verdict(payload.message_text)
    except AIServiceError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The analysis service is busy or unavailable. Please try again in a minute.",
        )
    except AIOutputError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The analysis returned an unexpected result. Please try again.",
        )

    stored_text = redact(payload.message_text)
    with get_connection() as conn:
        row = conn.execute(
            "INSERT INTO checks (user_id, message_text, risk_level, summary, next_steps) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (user["id"], stored_text, verdict.risk_level, verdict.summary, verdict.next_steps),
        ).fetchone()
        for flag in verdict.red_flags[:10]:
            conn.execute(
                "INSERT INTO red_flags (check_id, type, explanation) VALUES (%s, %s, %s)",
                (row["id"], flag.type, flag.explanation),
            )
        return _get_check_detail(conn, row["id"], user["id"])


@router.get("", response_model=list[CheckSummary])
def list_checks(user=Depends(get_current_user)):
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, risk_level, summary, feedback, created_at "
            "FROM checks WHERE user_id = %s ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()


@router.get("/{check_id}", response_model=CheckDetail)
def get_check(check_id: int, user=Depends(get_current_user)):
    with get_connection() as conn:
        return _get_check_detail(conn, check_id, user["id"])


@router.delete("/{check_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_check(check_id: int, user=Depends(get_current_user)):
    with get_connection() as conn:
        deleted = conn.execute(
            "DELETE FROM checks WHERE id = %s AND user_id = %s RETURNING id",
            (check_id, user["id"]),
        ).fetchone()
    if deleted is None:
        raise HTTPException(status_code=404, detail="Check not found")
@router.patch("/{check_id}/feedback", response_model=CheckDetail)
def set_feedback(check_id: int, payload: FeedbackUpdate, user=Depends(get_current_user)):
    with get_connection() as conn:
        updated = conn.execute(
            "UPDATE checks SET feedback = %s WHERE id = %s AND user_id = %s RETURNING id",
            (payload.feedback, check_id, user["id"]),
        ).fetchone()
        if updated is None:
            raise HTTPException(status_code=404, detail="Check not found")
        return _get_check_detail(conn, check_id, user["id"])