from fastapi import FastAPI, HTTPException, status, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from bson.objectid import ObjectId
# from fastapi_pagination import Page, add_pagination
# from fastapi_pagination.ext.pymongo import paginate
from typing import List
import math
from utils.database import connect_to_db
from utils.models import (
    LogInDetails,
    Category,
    CategoryOut,
    BlogPost,
    BlogPostOut,
    BlogPostOutMultiple,
    Admin,
    Product,
    ProductOut,
    ProductMultiple,
    EmailNewsletter,
)

# initialize app
app = FastAPI()

"""SET UP CORS"""
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

database = connect_to_db()
PAGINATION_PER_PAGE = 10

# auth helpers
def VALIDATE_TOKEN(token):
    auth_collection = database["admin_collection"]
    match = auth_collection.find_one({"token": token})
    if match is not None:
        return match
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin token not found"
        )


@app.post("/api/validate_token/", status_code=status.HTTP_200_OK)
def validate_toke(token: str = Header()):
    if VALIDATE_TOKEN(token):
        return {"status": True, "valid": True}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token Invalid"
        )


@app.post("/api/auth/login/", status_code=status.HTTP_200_OK)
def login_admin(login: LogInDetails):
    auth_collection = database["admin_collection"]
    login_detail_dict = login.model_dump()  # from user
    given_pword = login_detail_dict.get("password")
    given_email = login_detail_dict.get("email")

    data = auth_collection.find_one({"email": given_email})  # from db
    if data == None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Details not found"
        )
    if data.get("password") == given_pword:
        return {"status": True, "token": data.get("token")}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Details not found"
        )


# root
@app.get("/")
def root():
    return {"message": "Hello Fruitful Vine!"}


"""
CATEGORY APIS
"""


@app.post(
    "/api/category/", 
    status_code=status.HTTP_201_CREATED,
    response_model=dict
)
def create_category(category: Category, token: str = Header()):
    if VALIDATE_TOKEN(token):
        category_data = category.model_dump()
        category_collection = database['blog_categories_collection']
        try:
            category_collection.insert_one(category_data)
            return {"status": True}
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create catgory",
            )

@app.get(
    "/api/category/", 
    response_model=List[CategoryOut]
)
def get_categories():
    category_collection = database['blog_categories_collection']
    data = list(category_collection.find({}))
    for d in data:
        d["_id"] = str(d["_id"])
    return data


@app.delete(
    "/api/category/{c_id}/", 
    status_code=status.HTTP_200_OK,
    response_model=dict
)
def delete_category(c_id: str, token: str = Header()):
    if VALIDATE_TOKEN(token):
        category_collection = database['blog_categories_collection']
        data = category_collection.find_one({"_id": ObjectId(c_id)})
        if data == None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
            )
        category_collection.delete_one(data)
        return {"status": True}

@app.put(
    "/api/category/{c_id}/", 
    status_code=status.HTTP_200_OK,
    response_model=dict
)
def update_category(c_id: str, category: Category, token: str = Header()):
    VALIDATE_TOKEN(token)

    category_data = category.model_dump()
    category_collection = database['blog_categories_collection']
    data_target = category_collection.find_one({"_id": ObjectId(c_id)})
    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Resource not found"
        )
    category_collection.update_one(
        {"_id": ObjectId(c_id)},
        {
            "$set": {
                "name": category_data.get("name"),
                "description": category_data.get("description"),
            }
        },
    )
    return {"status": True}


"""
 BLOG APIS
"""


@app.post(
    "/api/blog/",
    status_code=status.HTTP_201_CREATED,
    response_model=dict
)
def create_blog(blog: BlogPost, token: str = Header()):
    VALIDATE_TOKEN(token)
    blog_collection = database["blog_posts_collection"]
    blog_collection.insert_one(blog.model_dump())

    return {"status": True}


@app.post(
    "/api/edit_blog_content/{b_id}", 
    status_code=status.HTTP_200_OK,
    response_model=BlogPostOut
)
def edit_blog_content(
    blog_content: BlogPost, 
    b_id: str, 
    token: str = Header()
):
    VALIDATE_TOKEN(token)

    blog_data = blog_content.model_dump()
    blog_collection = database["blog_posts_collection"]
    data_target = blog_collection.find_one({"_id": ObjectId(b_id)})
    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    blog_collection.update_one(
        {"_id": ObjectId(b_id)},
        {
            "$set": {
                "image_url": blog_data.get("image_url"),
                "post_title": blog_data.get("post_title"),
                "category_name": blog_data.get("category_name"),
                "category_id": blog_data.get("category_id"),
                "short_title": blog_data.get("short_title"),
                "body": blog_data.get("body"),
                "iframe": blog_data.get("iframe"),
            }
        },
    )
    data_output = blog_collection.find_one({"_id": ObjectId(b_id)})
    data_output["_id"] = str(data_output["_id"])
    return data_output


# GET SPECIFIC BLOG POST
@app.get(
    "/api/get_blog_content/{b_id}", 
    status_code=status.HTTP_200_OK,
    response_model=BlogPostOut
)
def get_blog_content(b_id: str):
    blog_collection = database["blog_posts_collection"]
    data_target = blog_collection.find_one({"_id": ObjectId(b_id)})
    data_target["_id"] = str(data_target["_id"])

    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    
    return data_target


# GET ALL BLOG CONTENTS
@app.get(
    "/api/get_blog_posts/",
    response_model=BlogPostOutMultiple,
)
def get_blog_posts(page: int = 1, limit: int = 15):
    blog_collection = database["blog_posts_collection"]

    # guardrails
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    total_docs = blog_collection.count_documents({})
    total_pages = math.ceil(total_docs / limit)

    cursor = (
        blog_collection
        .find({})
        .sort("_id", -1)
        .skip(skip)
        .limit(limit)
    )

    blogs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        blogs.append(doc)
        
    return {
        "blogs": blogs,
        "pages": total_pages,
        "current_page": page
    }


@app.get(
    "/api/get_blog_posts_by_category/",
    response_model=BlogPostOutMultiple,
)
def get_blog_posts_by_category(
    category_id: str,
    page: int = 1, 
    limit: int = 15
):
    blog_collection = database["blog_posts_collection"]

    # guardrails
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    total_docs = blog_collection.count_documents({})
    total_pages = math.ceil(total_docs / limit)

    cursor = (
        blog_collection
        .find({"category_id":str(category_id)})
        .sort("_id", -1)
        .skip(skip)
        .limit(limit)
    )

    blogs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        blogs.append(doc)
        
    return {
        "blogs": blogs,
        "pages": total_pages,
        "current_page": page
    }


# DELETE blog CONTENT
@app.delete(
    "/api/del_blog_post/{b_id}/",
    status_code=status.HTTP_200_OK
)
def delete_blog_post(b_id: str, token: str = Header()):
    VALIDATE_TOKEN(token)
    blog_collection = database["blog_posts_collection"]
    data = blog_collection.find_one({"_id": ObjectId(b_id)})
    if data == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    blog_collection.delete_one(data)
    return {"status": True}


# GET LAST BLOG POST
@app.get(
    "/api/get_last_post/", 
    response_model=BlogPostOut
)
def get_last_post():
    blog_collection = database["blog_posts_collection"]
    last_post = blog_collection.find_one(
        {},
        sort=[("_id", -1)]
    )

    if not last_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No blog posts found"
        )

    last_post["_id"] = str(last_post["_id"])
    return last_post


@app.get(
    "/api/get_recent_posts/",
    response_model=BlogPostOutMultiple
)
def get_recent_posts(limit: int = 3):
    blog_collection = database["blog_posts_collection"]

    cursor = (
        blog_collection
        .find({})
        .sort("_id", -1)
        .limit(limit)
    )

    blogs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        blogs.append(doc)

    return {
        "blogs": blogs
    }


"""
PRODUCTS
"""

@app.post(
    "/api/product/",
    status_code=status.HTTP_201_CREATED,
    response_model=dict
)
def create_product(product: Product, token: str = Header()):
    VALIDATE_TOKEN(token)
    product_collection = database["products_collection"]
    product_collection.insert_one(product.model_dump())
    return {"status": True}


@app.post(
    "/api/edit_product/{b_id}", 
    status_code=status.HTTP_200_OK,
    response_model=ProductOut
)
def edit_product(
    product_content: Product, 
    b_id: str, 
    token: str = Header()
):
    VALIDATE_TOKEN(token)

    product_data = product_content.model_dump()
    product_collection = database["products_collection"]
    data_target = product_collection.find_one({"_id": ObjectId(b_id)})
    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    product_collection.update_one(
        {"_id": ObjectId(b_id)},
        {
            "$set": {
                "image_url": product_data.get("image_url"),
                "product_name": product_data.get("product_name"),
                "category_name": product_data.get("category_name"),
                "category_id": product_data.get("category_id"),
                "short_description": product_data.get("short_description"),
                "body": product_data.get("body"),
                "iframe": product_data.get("iframe"),
            }
        },
    )
    data_output = product_collection.find_one({"_id": ObjectId(b_id)})
    data_output["_id"] = str(data_output["_id"])
    return data_output


@app.get(
    "/api/get_product/{b_id}", 
    status_code=status.HTTP_200_OK,
    response_model=ProductOut
)
def get_product(b_id: str):
    product_collection = database["products_collection"]
    data_target = product_collection.find_one({"_id": ObjectId(b_id)})
    data_target["_id"] = str(data_target["_id"])

    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    
    return data_target


@app.get(
    "/api/get_products/",
    response_model=ProductMultiple,
)
def get_products(page: int = 1, limit: int = 15):
    product_collection = database["products_collection"]

    # guardrails
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    total_docs = product_collection.count_documents({})
    total_pages = math.ceil(total_docs / limit)

    cursor = (
        product_collection
        .find({})
        .sort("_id", -1)
        .skip(skip)
        .limit(limit)
    )

    blogs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        blogs.append(doc)
        
    return {
        "blogs": blogs,
        "pages": total_pages,
        "current_page": page
    }


@app.get(
    "/api/get_product_by_category/",
    response_model=ProductMultiple,
)
def get_product_by_category(
    category_id: str,
    page: int = 1, 
    limit: int = 15
):
    product_collection = database["products_collection"]

    # guardrails
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    total_docs = product_collection.count_documents({})
    total_pages = math.ceil(total_docs / limit)

    cursor = (
        product_collection
        .find({"category_id":str(category_id)})
        .sort("_id", -1)
        .skip(skip)
        .limit(limit)
    )

    blogs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        blogs.append(doc)
        
    return {
        "products": blogs,
        "pages": total_pages,
        "current_page": page
    }


@app.delete(
    "/api/del_product/{b_id}/",
    status_code=status.HTTP_200_OK
)
def delete_product(b_id: str, token: str = Header()):
    VALIDATE_TOKEN(token)
    product_collection = database["products_collection"]
    data = product_collection.find_one({"_id": ObjectId(b_id)})
    if data == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    product_collection.delete_one(data)
    return {"status": True}


@app.get(
    "/api/get_last_product/", 
    response_model=ProductOut
)
def get_last_product():
    product_collection = database["products_collection"]
    last_post = product_collection.find_one(
        {},
        sort=[("_id", -1)]
    )

    if not last_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No blog posts found"
        )

    last_post["_id"] = str(last_post["_id"])
    return last_post


@app.get(
    "/api/get_recent_product/",
    response_model=ProductMultiple
)
def get_recent_products(limit: int = 3):
    product_collection = database["products_collection"]

    cursor = (
        product_collection
        .find({})
        .sort("_id", -1)
        .limit(limit)
    )

    products = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        products.append(doc)

    return {
        "products": products
    }


"""
CONTACT US
"""

# Create

# Get all

# Get one
