from fastapi import APIRouter, Depends, HTTPException, status

from database import get_connection
from dependencies import get_current_user
from models import CheckCreate, CheckDetail, CheckSummary

router = APIRouter(prefix="/checks", tags=["checks"])

# TEMPORARY fake verdict, replaced by the AI on Day 7
FAKE_VERDICT = {
    "risk_level": "medium",
    "summary": "Placeholder verdict (AI not connected yet).",
    "next_steps": "Do not click links or share OTPs.",
    "red_flags": [{"type": "placeholder", "explanation": "Example red flag."}],
}


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
    v = FAKE_VERDICT
    with get_connection() as conn:
        row = conn.execute(
            "INSERT INTO checks (user_id, message_text, risk_level, summary, next_steps) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (user["id"], payload.message_text, v["risk_level"], v["summary"], v["next_steps"]),
        ).fetchone()
        for f in v["red_flags"]:
            conn.execute(
                "INSERT INTO red_flags (check_id, type, explanation) VALUES (%s, %s, %s)",
                (row["id"], f["type"], f["explanation"]),
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