"""Qualification and Evidence Cards Router for GeoDrill Pro v0.9."""
from fastapi import APIRouter, HTTPException
from packages.engineering.qualification import list_qualification_cards, get_qualification_card

router = APIRouter(prefix="/api/v1/qualification", tags=["Qualification"])


@router.get("/cards")
def get_all_cards():
    return list_qualification_cards()


@router.get("/cards/{module_id}")
def get_single_card(module_id: str):
    card = get_qualification_card(module_id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Qualification card '{module_id}' not found")
    return card
