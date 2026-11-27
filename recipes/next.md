# Recipes API — Next Steps

Roadmap of remaining endpoints and fixes.
Last reviewed against the current `recipes/recipes.py` and `recipes/model.py`.

---

## 0. Remaining fixes in existing routes

### Done
- `create_recipe` — now accepts `steps: list[str]` and builds `Steps(steps=...)`. ✓
- `update_recipe` — now has a 404 guard, `db.commit()`, `db.refresh()`, and returns the updated body. ✓
- `delete_recipe` — now deletes + commits, with a 404 guard and rollback. ✓

### `update_recipe` — still to fix
- `steps: str` should be `steps: list[str]` (a string is iterated character-by-character).
- `if not steps:` is inverted. It should be `if steps:` so the block runs when steps *are* provided.
- `recipe.steps = [step for step in steps]` creates a list of raw values, not `Steps` rows. Use:
  ```python
  if steps:
      recipe.steps = [Steps(steps=step) for step in steps]
  ```
- Method is `POST /{recipe_id}`; prefer `PATCH /{recipe_id}`.
- Add `db.rollback()` in the `except` block.
- `name: str` is a required query param, so callers can't update only the ingredients. Make the fields optional / use the Pydantic pattern below.

### `delete_recipe` — still to fix
- `status_code=204` must not return a body. Either `return None` (with 204) or switch to `200` and keep the JSON message. Returning `{"message": ...}` under 204 is a protocol violation.

### `create_recipe` — minor
- Add `db.rollback()` in the `except` block.
- `PUT /` (create) -> prefer `POST /` for convention.

### Partial-update pattern (for `update_recipe`)
```python
class RecipeUpdate(BaseModel):
    name: str | None = None
    ingredients: dict[str, float] | None = None
    steps: list[str] | None = None

@router.patch("/{recipe_id}")
def update_recipe(
    recipe_id: int,
    payload: RecipeUpdate,
    db: Session = Depends(database.get_db),
):
    ...
    # only fields the client actually sent:
    data = payload.model_dump(exclude_unset=True)
    if "name" in data:
        recipe.name = data["name"]
    if "ingredients" in data:
        recipe.ingredients = [
            Ingredients(ingredient=ing, amount=amount)
            for ing, amount in data["ingredients"].items()
        ]
    if "steps" in data:
        recipe.steps = [Steps(steps=step) for step in data["steps"]]
```

---

## 1. Sub-resource CRUD for ingredients (and steps)  — TODO

`Ingredients` / `Steps` already have their own ids, so expose them directly
instead of only supporting "replace the whole list" on the parent route.

| Method | Path | Purpose |
|---|---|---|
| `POST`   | `/{recipe_id}/ingredients` | add one ingredient |
| `PATCH`  | `/{recipe_id}/ingredients/{ingredient_id}` | change name/amount |
| `DELETE` | `/{recipe_id}/ingredients/{ingredient_id}` | remove one |
| `POST`   | `/{recipe_id}/steps` | add one step |
| `PATCH`  | `/{recipe_id}/steps/{step_id}` | edit one |
| `DELETE` | `/{recipe_id}/steps/{step_id}` | remove one |

Example:
```python
@router.post("/{recipe_id}/ingredients", status_code=201)
def add_ingredient(
    recipe_id: int,
    payload: IngredientIn,
    db: Session = Depends(database.get_db),
):
    recipe = db.get(Names, recipe_id)
    if not recipe:
        return response("Not found", 404)

    row = Ingredients(
        recipe_id=recipe_id,
        ingredient=payload.ingredient,
        amount=payload.amount,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.to_dict()
```

Tradeoff: replace-all (one request) vs sub-resources (more requests, but no
orphan handling and safer concurrent edits). You can keep both.

---

## 2. Search & filtering on the list route  — TODO

Extend `GET /` with query params rather than new paths:

- `?q=chicken` -> `Names.name.ilike(f"%{q}%")`
- `?ingredient=tomato` -> join `Ingredients` and filter
- `?sort=name` / `?order=asc`
- `?max_ingredients=5`

---

## 3. Count / metadata  — TODO

`GET /count` -> `{"count": db.query(Names).count()}`

Pairs with the existing `limit`/`offset` for pagination UIs.

---

## 4. Convenience routes  — TODO

- `GET /random` — `db.query(Names).order_by(func.random()).first()`
  (Postgres; use `func.rand()` on SQLite)
- `POST /{recipe_id}/duplicate` — clone a recipe (reuses child-creation code)
- `POST /bulk` — create many recipes in one transaction

---

## 5. Route-ordering trap

Static routes (`/count`, `/random`) MUST be declared **before** `/{recipe_id}`,
or FastAPI matches `count` as `recipe_id` and fails with a 422 (not an int).

```python
@router.get("/count")        # first
...
@router.get("/random")       # then
...
@router.get("/{recipe_id}")  # catch-all last
```

---

## 6. Cascade requirement (model.py)  — still TODO

`model.py` still uses plain `backref="ingredients"` / `backref="steps"` with no
cascade. Replacing or clearing child rows (as `update_recipe` does) leaves old
rows behind with `recipe_id = NULL`. Add delete-orphan cascade:

```python
from sqlalchemy.orm import relationship, backref

# in Ingredients and Steps
recipe = relationship(
    "Names", backref=backref("ingredients", cascade="all, delete-orphan")
)
# and
recipe = relationship(
    "Names", backref=backref("steps", cascade="all, delete-orphan")
)
```

Alternative (DB-level, needs a migration):
`ForeignKey("names.id", ondelete="CASCADE")` + `passive_deletes=True`.

---

## Not worth adding yet

Auth, API versioning, ETags, export/PDF — real eventually, but they add
surface area before the core CRUD is clean.

---

## Suggested implementation order

1. Finish `update_recipe`: `steps: list[str]`, `if steps:`, build `Steps(steps=...)`,
   add `db.rollback()`.
2. Fix `delete_recipe` (204 body) — either `return None` or use `200`.
3. Add delete-orphan cascade in `model.py` (section 6).
4. Convert update to `PATCH /{recipe_id}` with Pydantic `exclude_unset` (section 0).
5. Ingredient sub-routes (`POST` / `PATCH` / `DELETE`).
6. `GET /count`, then `GET /random` (mind section 5 ordering).
7. Search/filter params on `GET /`.
8. Rename `PUT /` -> `POST /` for create.
