# Recipes API — Next Steps

Roadmap of endpoints and fixes to implement, roughly in priority order.
Based on `recipes/recipes.py` and `recipes/model.py`.

---

## 0. Fix the existing surface first

New endpoints will inherit the same confusion if these aren't cleaned up.

### Bugs to fix
- `create_recipe` — `Steps(step=step)` should be `Steps(steps=step)` (the column is `steps`).
- `create_recipe` — `steps: str` is iterated character-by-character; change to `steps: list[str]`.
- `update_recipe` — inverted `if not name:` (updates only when empty). Use presence checks.
- `update_recipe` — never calls `db.commit()`, so changes are discarded.
- `update_recipe` — no 404 guard; `db.get()` can return `None`.
- `delete_recipe` — body is `pass`; it deletes nothing.

### Semantics / conventions
- `PUT /` (create) -> prefer `POST /`.
- `POST /{recipe_id}` (update) -> prefer `PATCH /{recipe_id}` (partial update).
- `DELETE /{recipe_id}` -> return `204 No Content`, or keep `200` but be consistent.

### Partial-update pattern
```python
class RecipeUpdate(BaseModel):
    name: str | None = None
    ingredients: dict[str, float] | None = None
    steps: list[str] | None = None

# only fields the client actually sent:
data = payload.model_dump(exclude_unset=True)
if "name" in data:
    recipe.name = data["name"]
```

---

## 1. Sub-resource CRUD for ingredients (and steps)

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

## 2. Search & filtering on the list route

Extend `GET /` with query params rather than new paths:

- `?q=chicken` -> `Names.name.ilike(f"%{q}%")`
- `?ingredient=tomato` -> join `Ingredients` and filter
- `?sort=name` / `?order=asc`
- `?max_ingredients=5`

---

## 3. Count / metadata

`GET /count` -> `{"count": db.query(Names).count()}`

Pairs with the existing `limit`/`offset` for pagination UIs.

---

## 4. Convenience routes

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

## 6. Cascade requirement (model.py)

Replacing or deleting child rows requires delete-orphan cascade, otherwise old
`Ingredients` / `Steps` rows are left behind with `recipe_id = NULL`:

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

1. Fix the existing bugs in section 0 (commit, 404s, `steps` column, delete).
2. Add delete-orphan cascade in `model.py` (section 6).
3. `PATCH /{recipe_id}` partial update via `exclude_unset`.
4. Ingredient sub-routes (`POST` / `PATCH` / `DELETE`).
5. `GET /count`, then `GET /random`.
6. Search/filter params on `GET /`.
