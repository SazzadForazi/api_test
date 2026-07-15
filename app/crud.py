from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator

from app.auth import get_current_user, UserProfile

router = APIRouter(prefix="/api/v1/products", tags=["Products & CRUD"])

# Initial state
INITIAL_PRODUCTS = [
    {
        "id": 1,
        "name": "Wireless Mouse",
        "price": 25.99,
        "category": "Electronics",
        "in_stock": True,
        "description": "Ergonomic 2.4GHz wireless mouse."
    },
    {
        "id": 2,
        "name": "Mechanical Keyboard",
        "price": 79.99,
        "category": "Electronics",
        "in_stock": True,
        "description": "RGB mechanical keyboard with blue switches."
    },
    {
        "id": 3,
        "name": "Running Shoes",
        "price": 59.90,
        "category": "Footwear",
        "in_stock": False,
        "description": "Lightweight breathable running shoes."
    },
    {
        "id": 4,
        "name": "Coffee Mug",
        "price": 12.50,
        "category": "Kitchenware",
        "in_stock": True,
        "description": "Ceramic travel coffee mug."
    }
]

# In-memory "database"
products_db = [dict(item) for item in INITIAL_PRODUCTS]
current_id = 4

# Pydantic Schemas for Validation
class ProductBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=100, json_schema_extra={"example": "Wireless Mouse"})
    price: float = Field(..., gt=0, json_schema_extra={"example": 29.99})
    category: str = Field(..., min_length=2, json_schema_extra={"example": "Electronics"})
    in_stock: bool = Field(default=True, json_schema_extra={"example": True})
    description: Optional[str] = Field(default=None, json_schema_extra={"example": "Product description here."})

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str):
        allowed = ["Electronics", "Footwear", "Kitchenware", "Books", "Clothing"]
        if value not in allowed:
            raise ValueError(f"Category must be one of: {', '.join(allowed)}")
        return value

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=2)
    in_stock: Optional[bool] = None
    description: Optional[str] = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str):
        if value is None:
            return value
        allowed = ["Electronics", "Footwear", "Kitchenware", "Books", "Clothing"]
        if value not in allowed:
            raise ValueError(f"Category must be one of: {', '.join(allowed)}")
        return value

class Product(ProductBase):
    id: int

# Dependency for role verification
def require_roles(allowed_roles: List[str]):
    def dependency(current_user: UserProfile = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required role(s): {', '.join(allowed_roles)}. You are: {current_user.role}"
            )
        return current_user
    return dependency

# Endpoints
@router.get("", response_model=List[Product])
def list_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max number of products to return"),
    category: Optional[str] = Query(None, description="Filter products by category"),
    in_stock: Optional[bool] = Query(None, description="Filter products by in stock status"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    q: Optional[str] = Query(None, description="Search term for name or description")
):
    results = products_db
    
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if in_stock is not None:
        results = [p for p in results if p["in_stock"] == in_stock]
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if q:
        q_lower = q.lower()
        results = [
            p for p in results 
            if q_lower in p["name"].lower() or (p["description"] and q_lower in p["description"].lower())
        ]
        
    return results[skip : skip + limit]

@router.get("/{product_id}", response_model=Product)
def get_product(product_id: int):
    for product in products_db:
        if product["id"] == product_id:
            return product
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product with ID {product_id} not found."
    )

@router.post("", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    current_user: UserProfile = Depends(require_roles(["tester", "admin"]))
):
    global current_id
    current_id += 1
    new_product = {
        "id": current_id,
        **product_in.model_dump()
    }
    products_db.append(new_product)
    return new_product

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    current_user: UserProfile = Depends(require_roles(["tester", "admin"]))
):
    for product in products_db:
        if product["id"] == product_id:
            update_data = product_in.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                product[field] = value
            return product
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product with ID {product_id} not found."
    )

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: UserProfile = Depends(require_roles(["admin"]))
):
    global products_db
    for index, product in enumerate(products_db):
        if product["id"] == product_id:
            products_db.pop(index)
            return {"message": f"Product with ID {product_id} has been deleted."}
            
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product with ID {product_id} not found."
    )

@router.post("/reset")
def reset_products():
    global products_db, current_id
    products_db = [dict(item) for item in INITIAL_PRODUCTS]
    current_id = len(products_db)
    return {"message": "Database reset to initial test data."}
