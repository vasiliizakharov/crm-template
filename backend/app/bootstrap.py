"""Idempotent bootstrap: creates the admin user if missing."""
import logging
import sys

from sqlalchemy import select

from .config import settings
from .database import session_scope
from . import models, auth

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("bootstrap")


def main():
    if not settings.admin_password:
        log.error("ADMIN_PASSWORD is empty — refusing to create an admin without a password. "
                  "Set ADMIN_PASSWORD in the environment before starting.")
        sys.exit(1)

    with session_scope() as db:
        existing = db.scalar(select(models.User).where(models.User.email == settings.admin_email))
        if existing:
            log.info("Admin %s already exists, id=%s", settings.admin_email, existing.id)
            # Update password if supplied and different (initial-deployment policy).
            if settings.admin_password and not auth.verify_password(settings.admin_password, existing.password_hash):
                existing.password_hash = auth.hash_password(settings.admin_password)
                log.info("Admin password updated.")
            return
        u = models.User(
            email=settings.admin_email,
            full_name=settings.admin_full_name,
            password_hash=auth.hash_password(settings.admin_password),
            role="admin",
            is_active=True,
        )
        db.add(u)
        log.info("Admin created: %s", settings.admin_email)


if __name__ == "__main__":
    main()
