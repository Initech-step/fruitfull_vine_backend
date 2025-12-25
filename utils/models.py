from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

# shared models
class OutputModel(BaseModel):
    id: str = Field(alias="_id")

class PaginationAndStatus(BaseModel):
    status: bool = True
    no_of_pages: int = 0
    current_page: int = 0

# specific models
class Category(BaseModel):
    name: str
    description: str

class CategoryOutputModel(OutputModel):
    name: str
    description: str

class CategoryOut(PaginationAndStatus):
    data: list[CategoryOutputModel]


class EmailNewsletter(BaseModel):
    email: str


class ImageGroup(BaseModel):
    title: str
    description: str


class ImageModel(BaseModel):
    orignal_filename: str
    url: str
    asset_id: str
    image_title: str
    image_group_id: str


class BlogPost(BaseModel):
    image_url: str
    category_id: str
    category_name: str
    post_title: str
    short_title: str
    body: str
    date: str = Field(default=str(date.today()))
    video: bool = False
    iframe: str


class PageContent(BaseModel):
    image_url: str
    content_title: str
    body: str
    page: str


class Admin(BaseModel):
    email: str
    password: str
    token: str


class LogInDetails(BaseModel):
    email: str
    password: str


