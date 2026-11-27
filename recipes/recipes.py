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


@router.get("/{recipe_id}", tags=["recipes"], status_code=200)
def get_recipe(recipe_id: int, db: Session = Depends(database.get_db)):
    try:
        recipe = db.get(Names, recipe_id)
        if not recipe:
            return response("Not found", 404)

        return {
            **recipe.to_dict(),
            "ingredients": [ingredient.to_dict() for ingredient in recipe.ingredients],
            "steps": [step.to_dict() for step in recipe.steps],
        }
    except Exception as e:
        return response(str(e), 500)


@router.post("/", tags=["recipes"], status_code=201)
def create_recipe(
    name: str,
    ingredients: dict[str, float],
    steps: list[str],
    db: Session = Depends(database.get_db),
):
    try:
        if not name:
            return response("A recipe needs a name", 400)
        if not ingredients:
            return response("A recipe needs ingredients", 400)

        for ingredient, amount in ingredients.items():
            if amount <= 0:
                return response("Ingredient amount must be positive", 400)
            if ingredient == "":
                return response("Ingredient name cannot be empty", 400)

        recipe = Names(
            name=name,
            ingredients=[
                Ingredients(ingredient=ing, amount=amount)
                for ing, amount in ingredients.items()
            ],
            steps=[Steps(steps=step) for step in steps],
        )

        db.add(recipe)
        db.commit()
        db.refresh(recipe)
        return {
            **recipe.to_dict(),
            "ingredients": [ingredient.to_dict() for ingredient in recipe.ingredients],
            "steps": [step.to_dict() for step in recipe.steps],
        }
    except Exception as e:
        db.rollback()
        return response(str(e), 500)


@router.patch("/{recipe_id}", tags=["recipes"], status_code=200)
def update_recipe(
    recipe_id: int,
    name: str | None = None,
    ingredients: dict[str, float] | None = None,
    steps: list[str] | None = None,
    db: Session = Depends(database.get_db),
):
    try:
        recipe = db.get(Names, recipe_id)
        if not recipe:
            return response("Not found", 404)

        if name:
            recipe.name = name
        if ingredients:
            for ing, amount in ingredients.items():
                if amount <= 0:
                    return response("Ingredient amount must be positive", 400)
                if ing == "":
                    return response("Ingredient name cannot be empty", 400)

            recipe.ingredients = [
                Ingredients(ingredient=ing, amount=amount)
                for ing, amount in ingredients.items()
            ]

        if steps:
            recipe.steps = [Steps(steps=step) for step in steps]

        db.commit()
        db.refresh(recipe)

        return {
            **recipe.to_dict(),
            "ingredients": [ingredient.to_dict() for ingredient in recipe.ingredients],
            "steps": [step.to_dict() for step in recipe.steps],
        }

    except Exception as e:
        db.rollback()
        return response(str(e), 500)


@router.delete("/{recipe_id}", tags=["recipes"], status_code=204)
def delete_recipe(recipe_id: int, db: Session = Depends(database.get_db)):
    try:
        recipe = db.get(Names, recipe_id)

        if not recipe:
            return response("Not found", 404)

        db.delete(recipe)
        db.commit()
        return
    except Exception as e:
        db.rollback()
        return response(str(e), 500)


@router.post("/{recipe_id}/ingredients", status_code=200)
def add_ingredient(
    recipe_id: int,
    ingredient: str,
    amount: float,
    db: Session = Depends(database.get_db),
):
    try:
        recipe = db.get(Names, recipe_id)

        if not recipe:
            return response("Not found", 404)

    except Exception as e:
        db.rollback()
        return response(str(e), 500)


@router.patch("/{recipe_id}/ingredients/{ingredient_id}", status_code=200)
def change_ingredient(
    recipe_id: int,
    ingredient_id: int,
    ingredient: str,
    amount: float,
    db: Session = Depends(database.get_db),
):
    try:
        pass
    except Exception as e:
        db.rollback()
        return response(str(e), 500)


@router.delete("/{recipe_id}/ingredients/{ingredient_id}", status_code=204)
def delete_ingredient(
    recipe_id: int, ingredient_id: int, db: Session = Depends(database.get_db)
):
    try:
        pass
    except Exception as e:
        db.rollback()
        return response(str(e), 500)


@router.post("/{recipe_id}/steps", status_code=200)
def add_step(
    recipe_id: int,
    step: str,
    db: Session = Depends(database.get_db),
):
    try:
        pass
    except Exception as e:
        db.rollback()
        return response(str(e), 500)


@router.patch("/{recipe_id}/steps/{step_id}", status_code=200)
def change_step(
    recipe_id: int,
    step_id: int,
    step: str,
    db: Session = Depends(database.get_db),
):
    try:
        pass
    except Exception as e:
        db.rollback()
        return response(str(e), 500)


@router.delete("/{recipe_id}/steps/{step_id}", status_code=204)
def delete_step(recipe_id: int, step_id: int, db: Session = Depends(database.get_db)):
    try:
        pass
    except Exception as e:
        db.rollback()
        return response(str(e), 500)
