from fastapi import Depends
from fastapi.param_functions import Query
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from sqlalchemy.orm import Session

from recipes import database
from recipes.model import Ingredients, Names, Steps

router = APIRouter(prefix="/api/v1/recipes", tags=["recipes"])


# ---------------------- Helper Methods ----------------------
def response(msg: str, status_code: int):
    """Returns a JSONResponse with the given message and status code"""
    return JSONResponse(content={"error": msg}, status_code=status_code)


# ---------------------- Routes ----------------------
@router.get("/", tags=["recipes"], status_code=200)
async def get_recipes(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(database.get_db),
):
    try:
        recipes = db.query(Names).limit(limit).offset(offset)
        return [recipe.to_dict() for recipe in recipes]
    except Exception as e:
        return response(str(e), 500)

@router.get("/{recipe_id}", tags=["recipes"])
def get_recipe(recipe_id: int, db: Session = Depends(database.get_db)):
    try:
        pass
        # recipe = db.get() # how to approach this??
        # business logic: could grab everything for this, ingredients, steps, recipe name, so a triple join? then just present the information in a list? OR how else????


    except Exception as e:
        return response(str(e), 500)
