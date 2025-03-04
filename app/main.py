from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, Response, Depends, Cookie
from fastapi.responses import HTMLResponse
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal

from typing import Optional

import jwt
import base64
import json

from repository.user import UserRepository, User
from repository.flower import FlowerRepository, Flower
from repository.purchase import PurchaseRepository, Purchase

SECRET_KEY = "flower_shop"
ALGORITHM = "HS256"

Base.metadata.create_all(bind=engine)

app = FastAPI()
user = UserRepository()
flower = FlowerRepository()
purchase = PurchaseRepository()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# регистрация

@app.post("/signup")
async def post_signup(
    request: Request, 
    email: str = Form(),
    user_name: str = Form(),
    password: str = Form(),
    foto: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if email.strip() == "":
        result = {
            "result": "error",
            "message": "invalid email"
        }
        raise HTTPException(status_code=401, detail=result)
    elif user_name.strip() == "":
        result = {
            "result": "error",
            "message": "invalid user name"
        }
        raise HTTPException(status_code=401, detail=result)
    elif password.strip() == "":
        result = {
            "result": "error",
            "message": "invalid password"
        }
        raise HTTPException(status_code=401, detail=result)
    
    if user.find_user_by_email(db, email):
        result = {
            "result": "error",
            "message": "email was registered earley"
        }
        raise HTTPException(status_code=401, detail=result)
    foto_bytes = await foto.read() if foto else None
    new_user = User(name = user_name, password = password, email = email, foto = foto_bytes)
    user.add(db, new_user)
    result = {
        "result": "ok",
        "message": "New user created"
    }
    return result

# Авторизация

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username  # здесь username выступает как email
    password = form_data.password
    temp_user = user.find_user_by_email(db, email)
    if not temp_user:
        result = {
            "result": "error",
            "message": "invalid email"
        }
        raise HTTPException(status_code=401, detail=result)
    elif temp_user.password != password:
        result = {
            "result": "error",
            "message": "invalid password"
        }
        raise HTTPException(status_code=401, detail=result)
    # генерим токен и сохраняем в куки (авторизация)
    token = create_token(temp_user)
    result = {
            "result": "ok",
            "access_token": token
        }
    return result

# Токен авторизации
def create_token(user: User):
    payload = {
        'user_id': user.id,
        "exp": datetime.utcnow() + timedelta(hours=1) 
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

# Проверка авторизации
def get_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            result = {
                "result": "error",
                "message": "Invalid credentials"
            }
            raise HTTPException(status_code=401, detail=result)
        # Получаем данные пользователя (в виде словаря) из репозитория
        user_data = user.find_user_by_id(db, int(user_id))
        if not user_data:
            result = {
                "result": "error",
                "message": "User not found"
            }
            raise HTTPException(status_code=401, detail=result)
        # Преобразуем словарь в объект User, если необходимо
        if isinstance(user_data, dict):
            user_obj = User(**user_data)
        else:
            user_obj = user_data
        return user_obj
    except jwt.PyJWTError:
        result = {
                "result": "error",
                "message": "Invalid credentials"
        }
        raise HTTPException(status_code=401, detail=result)
    
# Профиль
@app.get("/profile")
async def profile(db: Session = Depends(get_db), current_user: User = Depends(get_user)):
    result = {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
    }
    foto_b64 = base64.b64encode(current_user.foto).decode() if current_user.foto else None
    result["foto"] = foto_b64
    return result

# Список цветов
@app.get("/flowers")
def get_flowers(db: Session = Depends(get_db)):
    flowers = flower.get_all(db)
    result = [{"id" : f.id, "name": f.name, "count": f.count, "price": f.price} for f in flowers]
    return result 

# Добавление в список нового цветка
@app.post("/flowers")
def post_flowers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user),
    flower_name: str = Form(),
    count: int = Form(),
    price: float = Form()
):
    # Если пользователь авторизован, он может добавить новый цветок в каталог
    new_flower = Flower(name = flower_name, count = count, price = price)
    new_flower_id = flower.add(db, new_flower)
    return {"flower_id": new_flower_id}

# Обновление цветка
@app.patch("/flowers/{flower_id}")
def update_flower(
    flower_id: int,
    name: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    count: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    current_flower = flower.get_by_id(db, flower_id)
    if not current_flower:
        result = {
            "result": "error",
            "message": "Flower not found"
        }
        raise HTTPException(status_code=401, detail=result)
    if name is None:
        result = {
            "result": "error",
            "message": "Empty name"
        }
        raise HTTPException(status_code=401, detail=result)
    
    if price is None:
        result = {
            "result": "error",
            "message": "Empty price"
        }
        raise HTTPException(status_code=401, detail=result)
    elif price <= 0:
        result = {
            "result": "error",
            "message": f"Invalid price {price}"
        }
        raise HTTPException(status_code=401, detail=result)
    
    if count is None:
        result = {
            "result": "error",
            "message": "Empty count"
        }
        raise HTTPException(status_code=401, detail=result)
    elif count <= 0:
        result = {
            "result": "error",
            "message": f"Invalid price {count}"
        }
        raise HTTPException(status_code=401, detail=result)
    current_flower.name = name
    current_flower.price = price
    current_flower.count = count
    flower.update(db, current_flower)
    return {"result": "ok", "message": "Flower updated"}

# удаление цветка
@app.delete("/flowers/{flower_id}")
def delete_flower(
    flower_id: int,
    db: Session = Depends(get_db)
):
    current_flower = flower.get_by_id(db, flower_id)
    if not current_flower:
        result = {
            "result": "error",
            "message": "Flower not found"
        }
        raise HTTPException(status_code=401, detail=result)
    flower.delete(db, current_flower)
    return {"result": "ok", "message": "Flower deleted"}

# Добавление цветка в корзину
@app.post("/cart/items")
def add_in_cart(
    request: Request,
    response: Response,
    flower_id: int = Form(),
    current_user: User = Depends(get_user)
):
    cart = []
    cart_cookie = request.cookies.get('cart')
    if cart_cookie:
        try: 
            cart = json.loads(cart_cookie)
        except:
            cart = []
    cart.append(flower_id)
    response.set_cookie(key = "cart", value = json.dumps(cart))
    return {"result": "ok", "message": "flower added to cart"}

# Просмотр корзины
@app.get("/cart/items")
def get_cart(request: Request, db:Session = Depends(get_db),  current_user: User = Depends(get_user)):
    cart = []
    cart_cookie = request.cookies.get("cart")
    if cart_cookie:
        try:
            cart = json.loads(cart_cookie)
        except:
            cart = []
    total = 0.0
    cart_flowers = []
    for flower_id in cart:
        flower_in_cart = flower.get_by_id(db, flower_id)
        if flower_in_cart:
            flower_in_cart.count = 1
            cart_flowers.append(flower_in_cart)
            total += flower_in_cart.price
    result = {
        "items": cart_flowers,
        "total_price": total
    }
    return result
# очищение корзины
@app.delete("/cart/items")
async def clear_cart(response: Response):
    response.delete_cookie("cart")
    return {"result": "ok", "message": "Empty cart"}

# Заказы
@app.post("/purchased")
async def purchase_items(
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user),
    cart: Optional[str] = Cookie(None)
):
    if cart:
        try:
            cart_list = json.loads(cart)
        except Exception:
            cart_list = []
    else:
        cart_list = []
    flowers_list = []
    total = 0
    for flower_id in cart_list:
        current_flower = flower.get_by_id(db, flower_id)
        flowers_list.append({"id": current_flower.id, "name": current_flower.name, "price": current_flower.price, "count": 1})
    
    purchase.add(db, Purchase(user_id=current_user.id, flowers=json.dumps(flowers_list)))
    response.delete_cookie("cart")
    return {"message": "Purchase successful"}

@app.get("/purchased")
async def get_purchased(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_user)
):
    purchases = purchase.get_by_user_id(db, User.id)
    items = []
    purchases_list = []
    for user_purchase in purchases:
        purchases_list[user_purchase.id]["items"] = json.loads(user_purchase.flowers)
    return {"purchased": purchases_list}





