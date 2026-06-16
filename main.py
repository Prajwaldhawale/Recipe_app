from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from sqlalchemy import create_engine, String, select
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
    Session
)

# ==========================================
# DATABASE
# ==========================================

engine = create_engine(
    "sqlite:///recipes.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


class Base(DeclarativeBase):
    pass


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)

    item_name: Mapped[str] = mapped_column(String(100))

    ingredients: Mapped[str] = mapped_column(String(1000))

    recipe: Mapped[str] = mapped_column(String(3000))


Base.metadata.create_all(bind=engine)

# ==========================================
# APP
# ==========================================

app = FastAPI()

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="frontend")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# HOME
# ==========================================

@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    db: Session = Depends(get_db)
):

    recipes = db.scalars(
        select(Recipe)
    ).all()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "recipes": recipes
        }
    )


# ==========================================
# CREATE PAGE
# ==========================================

@app.get("/create", response_class=HTMLResponse)
def create_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="create.html",
        context={}
    )


# ==========================================
# CREATE
# ==========================================

@app.post("/create")
def create_recipe(
    item_name: str = Form(...),
    ingredients: str = Form(...),
    recipe: str = Form(...),
    db: Session = Depends(get_db)
):

    new_recipe = Recipe(
        item_name=item_name,
        ingredients=ingredients,
        recipe=recipe
    )

    db.add(new_recipe)
    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )


# ==========================================
# UPDATE PAGE
# ==========================================

@app.get("/update/{recipe_id}", response_class=HTMLResponse)
def update_page(
    recipe_id: int,
    request: Request,
    db: Session = Depends(get_db)
):

    recipe = db.get(
        Recipe,
        recipe_id
    )

    if recipe is None:
        return HTMLResponse(
            content="Recipe not found",
            status_code=404
        )

    return templates.TemplateResponse(
        request=request,
        name="update.html",
        context={
            "recipe": recipe
        }
    )


# ==========================================
# UPDATE
# ==========================================

@app.post("/update/{recipe_id}")
def update_recipe(
    recipe_id: int,
    item_name: str = Form(...),
    ingredients: str = Form(...),
    recipe: str = Form(...),
    db: Session = Depends(get_db)
):

    recipe_obj = db.get(
        Recipe,
        recipe_id
    )

    if recipe_obj is None:
        return HTMLResponse(
            content="Recipe not found",
            status_code=404
        )

    recipe_obj.item_name = item_name
    recipe_obj.ingredients = ingredients
    recipe_obj.recipe = recipe

    db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )


# ==========================================
# DELETE
# ==========================================

@app.post("/delete/{recipe_id}")
def delete_recipe(
    recipe_id: int,
    db: Session = Depends(get_db)
):

    recipe = db.get(
        Recipe,
        recipe_id
    )

    if recipe:
        db.delete(recipe)
        db.commit()

    return RedirectResponse(
        url="/",
        status_code=303
    )