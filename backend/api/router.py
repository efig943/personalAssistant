"""
api/router.py
Central router aggregator — include_router() calls for every sub-module.
main.py only needs to import this single router.
"""
from fastapi import APIRouter

from backend.api import social, calendar, crm, settings

router = APIRouter()

router.include_router(social.router)
router.include_router(calendar.router)
router.include_router(crm.router)
router.include_router(settings.router)
