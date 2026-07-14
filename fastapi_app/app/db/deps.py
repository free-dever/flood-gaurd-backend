"""
Flood Guard — Database Session Dependency
==========================================
Provides a get_db() generator that FastAPI injects into any route
that declares it as a dependency.

How it works
------------
FastAPI calls get_db() before running the route function.
The session is created and yielded — the route receives it and
does its DB work. After the route finishes (success or error),
execution resumes after the yield and the session is closed.

Usage in a router
-----------------
    from fastapi import Depends
    from fastapi_app.app.db.deps import get_db
    from sqlalchemy.orm import Session

    @router.get("/example")
    def example(db: Session = Depends(get_db)):
        ...
"""

from collections.abc import Generator

from sqlalchemy.orm import Session

from shared.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session and guarantee it closes after the request,
    regardless of whether the request succeeded or raised an exception.
    """
    db = SessionLocal()
    try:
        yield db          # <-- route function runs here, with access to db
    finally:
        db.close()        # <-- always runs after the route, no matter what
