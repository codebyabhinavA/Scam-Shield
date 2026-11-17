import math

from fastapi import HTTPException, status

from database import get_connection

MAX_CHECKS_PER_HOUR = 20


def enforce_ai_limit(user_id: int) -> None:
    """Raise 429 if the user used up their hourly AI quota, else record one use."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT count(*) AS n, "
            "EXTRACT(EPOCH FROM (min(created_at) + interval '1 hour' - now())) AS retry_after "
            "FROM ai_usage WHERE user_id = %s AND created_at > now() - interval '1 hour'",
            (user_id,),
        ).fetchone()
        if row["n"] >= MAX_CHECKS_PER_HOUR:
            retry_after = max(1, math.ceil(row["retry_after"]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many checks. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )
        conn.execute("INSERT INTO ai_usage (user_id) VALUES (%s)", (user_id,))