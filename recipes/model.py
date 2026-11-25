from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm.properties import ForeignKey

from recipes.database import Base


class Names(Base):
    __tablename__ = "names"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    ingredients = relationship("Ingredients", backref="recipe")
    steps = relationship("Steps", backref="recipe")

    def to_dict(self):
        return {"id": self.id, "name": self.name}


class Ingredients(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("names.id"), index=True)

    ingredient = Column(String, nullable=True)
    amount = Column(Float, nullable=True)

    recipe = relationship("Names", backref="ingredients")

    def to_dict(self):
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "ingredient": self.ingredient,
            "amount": self.amount,
        }


class Steps(Base):
    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("names.id"), index=True)

    steps = Column(String)

    recipe = relationship("Names", backref="steps")

    def to_dict(self):
        return {"id": self.id, "recipe_id": self.recipe_id, "steps": self.steps}
