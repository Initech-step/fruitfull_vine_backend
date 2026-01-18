from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from enum import Enum


# shared models
class OutputModel(BaseModel):
    id: str = Field(alias="_id")


class CategoryType(Enum):
    product = "product"
    blog = "blog"


# specific models
class Category(BaseModel):
    name: str
    type: str  # should be either 'product' or 'blog'
    description: Optional[str] = None


class CategoryOut(OutputModel):
    name: str
    description: Optional[str] = None
    type: str


class EmailNewsletter(BaseModel):
    email: str


class BlogPostOut(OutputModel):
    url: Optional[str] = None
    secure_url: Optional[str] = None
    public_id: Optional[str] = None
    category_id: str
    category_name: str
    post_title: str
    short_title: str
    body: str
    date: Optional[str] = Field(default=str(date.today()))
    draft: bool = False


class BlogPostOutMultiple(BaseModel):
    current_page: int = 0
    pages: int = 0
    blogs: list[BlogPostOut] = []


class Admin(BaseModel):
    email: str
    password: str
    token: str


class LogInDetails(BaseModel):
    email: str
    password: str


class Images(BaseModel):
    url: str
    secure_url: str
    public_id: str


class ProductOut(OutputModel):
    images: List[Images] = []
    category_id: str
    category_name: str
    product_name: str
    short_description: str
    body: str
    date: str = Field(default=str(date.today()))


class ProductMultiple(BaseModel):
    current_page: int = 0
    pages: int = 0
    products: list[ProductOut] = []


class ContactUs(BaseModel):
    name: Optional[str]
    email: Optional[str]
    message: Optional[str]
    phone_number: str
    created_at: str = Field(default=str(date.today()))


class ContactOut(OutputModel):
    name: Optional[str]
    email: Optional[str]
    message: Optional[str]
    phone_number: str
    created_at: Optional[str] = None


class ContactMultiple(BaseModel):
    current_page: int = 0
    pages: int = 0
    contacts: list[ContactOut] = []
