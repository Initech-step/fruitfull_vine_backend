from fastapi import FastAPI, HTTPException, status, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from bson.objectid import ObjectId
from typing import List, Optional
import math
from datetime import datetime
from utils.database import connect_to_db
from utils.models import (
    LogInDetails,
    Category,
    CategoryOut,
    BlogPost,
    BlogPostOut,
    BlogPostOutMultiple,
    Product,
    ProductOut,
    ProductMultiple,
    EmailNewsletter,
    ContactUs,
    ContactOut,
    ContactMultiple,
    CategoryType
)
import os

# initialize app
app = FastAPI()

"""SET UP CORS"""
origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

database = connect_to_db()
offline = os.getenv("OFFLINE_MODE", False)
print(f"\n OFFLINE MODE: {offline} \n")
print(type(offline))
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
    if offline:
        print("Offline mode: skipping category creation")
        return {"status": True}
    
    if VALIDATE_TOKEN(token):
        category_data = category.model_dump()
        category_collection = database['categories_collection']
        try:
            category_collection.insert_one(category_data)
            return {"status": True}
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create catgory",
            )

@app.get(
    "/api/category/", 
    response_model=List[CategoryOut]
)
def get_categories(type:CategoryType = CategoryType.product):
    if offline:
        return [
            {
                "_id" : "64b8f4f2f2f2f2f2f2f2f2f2",
                "name": "Sample Category",
                "type": type.value,
                "description": "This is a sample category description.",
            },
            {
                "_id" : "ofiolnbkcr",
                "name": "Sample Category 2",
                "type": type.value,
                "description": "This is a sample category description.",
            },
            {
                "_id" : "k2i39i0r392ir8439",
                "name": "Sample Category 3",
                "type": type.value,
                "description": "This is a sample category description.",
            },
        ]
    category_collection = database['categories_collection']
    data = list(category_collection.find({"type": type.value}))
    for d in data:
        d["_id"] = str(d["_id"])
    return data


@app.delete(
    "/api/category/{c_id}/{type}/", 
    status_code=status.HTTP_200_OK,
    response_model=dict
)
def delete_category(
    c_id: str, 
    type: CategoryType = CategoryType.product, 
    token: str = Header()
):
    if offline:
        return {"status": True}
    
    if VALIDATE_TOKEN(token):
        # find and verify category
        category_collection = database['categories_collection']
        category_data = category_collection.find_one({"_id": ObjectId(c_id)})
        if category_data == None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
            )
        # check if linked to any products or blog posts
        if type == CategoryType.product:
            product_collection = database['products_collection']
            if product_collection.find_one({"category_id": ObjectId(c_id)}) is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category is linked to a product",
                )
            else:
                category_collection.delete_one({"_id": ObjectId(c_id)})

        if type == CategoryType.blog:
            # get the needed collections
            blog_posts_collection = database['blog_posts_collection']
            if blog_posts_collection.find_one({"category_id": ObjectId(c_id)}) is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category is linked to a blog post",
                )
            else:
                category_collection.delete_one({"_id": ObjectId(c_id)})
            
        return {"status": True}

@app.put(
    "/api/category/{c_id}/", 
    status_code=status.HTTP_200_OK,
    response_model=dict
)
def update_category(c_id: str, category: Category, token: str = Header()):
    if offline:
        return {"status": True}
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
    if offline:
        return {"status": True}
    VALIDATE_TOKEN(token)
    blog_collection = database["blog_posts_collection"]
    blog_collection.insert_one(blog.model_dump())

    return {"status": True}


@app.put(
    "/api/blog/{b_id}/", 
    status_code=status.HTTP_200_OK,
    response_model=BlogPostOut
)
def edit_blog_content(
    blog_content: BlogPost, 
    b_id: str, 
    token: str = Header()
):
    if offline:
        return {
            "_id": "k2i39i0r392ir8439", 
            "image_url": "https://example.com/image.jpg",
            "post_title": "Sample Post Title",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_title": "Sample Short Title",
            "body": "Sample blog post body content.",
            "iframe": "<iframe src='https://example.com'></iframe>",
        }
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

# GET ALL BLOG CONTENTS
@app.get(
    "/api/blog/",
    response_model=BlogPostOutMultiple,
)
def get_blog_posts(
    page: int = 1, 
    limit: int = 15,
    category_id: Optional[str] = None
):
    if offline:
        return {
            "blogs": [
                {
                    "_id": "k2i39i0r392ir8439", 
                    "image_url": "https://example.com/image.jpg",
                    "post_title": "Sample Post Title",
                    "category_name": "Sample Category",
                    "category_id": "sample_category_id",
                    "short_title": "Sample Short Title",
                    "body": "Sample blog post body content.",
                    "iframe": "<iframe src='https://example.com'></iframe>",
                },
                {
                    "_id": "oi23j4oij234oij234", 
                    "image_url": "https://example.com/image2.jpg",
                    "post_title": "Another Sample Post Title",
                    "category_name": "Another Sample Category",
                    "category_id": "another_sample_category_id",
                    "short_title": "Another Sample Short Title",
                    "body": "Another sample blog post body content.",
                    "iframe": "<iframe src='https://example.com'></iframe>",
                }
            ],
            "pages": 1,
            "current_page": 1
        }
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
    if category_id is not None:
        cursor = (
            blog_collection
            .find({"category_id": category_id})
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

# GET SPECIFIC BLOG POST
@app.get(
    "/api/blog/{b_id}/", 
    status_code=status.HTTP_200_OK,
    response_model=BlogPostOut
)
def get_blog_content(b_id: str):
    if offline:
        return {
            "_id": "k2i39i0r392ir8439", 
            "image_url": "https://example.com/image.jpg",
            "post_title": "Sample Post Title",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_title": "Sample Short Title",
            "body": "Sample blog post body content.",
            "iframe": "<iframe src='https://example.com'></iframe>",
        }
    blog_collection = database["blog_posts_collection"]
    data_target = blog_collection.find_one({"_id": ObjectId(b_id)})
    data_target["_id"] = str(data_target["_id"])

    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    
    return data_target

# DELETE blog CONTENT
@app.delete(
    "/api/blog/{b_id}/",
    status_code=status.HTTP_200_OK
)
def delete_blog_post(b_id: str, token: str = Header()):
    if offline:
        return {"status": True}
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
    if offline:
        return {
            "_id": "k2i39i0r392ir8439", 
            "image_url": "https://example.com/image.jpg",
            "post_title": "Sample Post Title",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_title": "Sample Short Title",
            "body": "Sample blog post body content.",
            "iframe": "<iframe src='https://example.com'></iframe>",
        }
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


"""
PRODUCTS
"""


@app.post(
    "/api/product/",
    status_code=status.HTTP_201_CREATED,
    response_model=dict
)
def create_product(product: Product, token: str = Header()):
    if offline:
        return {"status": True}
    VALIDATE_TOKEN(token)
    product_collection = database["products_collection"]
    product_collection.insert_one(product.model_dump())
    return {"status": True}

@app.get(
    "/api/products/",
    response_model=ProductMultiple,
)
def get_products(
    page: int = 1, 
    limit: int = 15,
    category_id: Optional[str] = None
):
    if offline:
        return {
            "products": [
                {
                    "_id": "k2i39i0r392ir8439", 
                    "image_url": "https://example.com/image.jpg",
                    "product_name": "Sample Product Name",
                    "category_name": "Sample Category",
                    "category_id": "sample_category_id",
                    "short_description": "Sample short description of the product.",
                    "body": "Detailed description of the sample product.",
                    "iframe": "<iframe src='https://example.com'></iframe>",
                },
                {
                    "_id": "oi23j4oij234oij234", 
                    "image_url": "https://example.com/image2.jpg",
                    "product_name": "Another Sample Product Name",
                    "category_name": "Another Sample Category",
                    "category_id": "another_sample_category_id",
                    "short_description": "Another sample short description of the product.",
                    "body": "Detailed description of another sample product.",
                }
            ],
            "pages": 1,
            "current_page": 1
        }

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
    if category_id is not None:
        cursor = (
            product_collection
            .find({"category_id": category_id})
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
    "/api/product/{p_id}/", 
    status_code=status.HTTP_200_OK,
    response_model=ProductOut
)
def get_product(p_id: str):
    if offline:
        return {
            "_id": "k2i39i0r392irrr8439", 
            "image_url": "https://example.com/image.jpg",
            "product_name": "Sample Product Name",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_description": "Sample short description of the product.",
            "body": "Detailed description of the sample product.",
            "iframe": "<iframe src='https://example.com'></iframe>",
        }
    product_collection = database["products_collection"]
    data_target = product_collection.find_one({"_id": ObjectId(p_id)})
    data_target["_id"] = str(data_target["_id"])

    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    
    return data_target

@app.get(
    "/api/get_last_product/", 
    response_model=ProductOut
)
def get_last_product():
    if offline:
        return {
            "_id": "k2i39i0r392irrr8439", 
            "image_url": "https://example.com/image.jpg",
            "product_name": "Sample Product Name",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_description": "Sample short description of the product.",
            "body": "Detailed description of the sample product.",
            "iframe": "<iframe src='https://example.com'></iframe>",
        }
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

@app.delete(
    "/api/product/{p_id}/",
    status_code=status.HTTP_200_OK
)
def delete_product(p_id: str, token: str = Header()):
    if offline:
        return {"status": True}
    
    VALIDATE_TOKEN(token)
    product_collection = database["products_collection"]
    data = product_collection.find_one({"_id": ObjectId(p_id)})
    if data == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    product_collection.delete_one(data)
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
    if offline:
        return {
            "_id": "k2i39i0r392irrr8439", 
            "image_url": "https://example.com/image.jpg",
            "product_name": "Sample Product Name",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_description": "Sample short description of the product.",
            "body": "Detailed description of the sample product.",
            "iframe": "<iframe src='https://example.com'></iframe>",
        }
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


"""
CONTACT US
"""
# TODO: PRODUCT Filtering by price or other stats
 
@app.post(
    "/api/contact/",
    status_code=201,
    response_model=dict
)
def create_contact(contact: ContactUs):
    if offline:
        return {"status": True}
    data = contact.model_dump()
    contact_collection = database["contact_collection"]
    contact_collection.insert_one(data)
    return {"status": True}


@app.get(
    "/api/contact/",
    response_model=ContactMultiple
)
def get_all_contacts():
    if offline:
        return {
            "current_page": 0,
            "pages": 0,
            "contacts": [
                {
                    "_id": "k2i39i0r392ir8439",
                    "name": "John Doe",
                    "email": "etimitest@gmailcpom",
                    "message": "Hello, I would like to know more about your products.",
                    "phone_number": "+1234567890",
                    "created_at": "2024-01-01"
                },
                {
                    "_id": "k2jwesccmsi39i0r392ir8439",
                    "name": "John Rugged",
                    "email": "etimitest@gmailcpom",
                    "message": "Hello, I would like to know more about your products.",
                    "phone_number": "+1234567890",
                    "created_at": "2024-01-01"
                },
            ]
        }

    contact_collection = database["contact_collection"]
    data = list(contact_collection.find({}).sort("created_at", -1))
    for d in data:
        d["_id"] = str(d["_id"])
    return {
        "current_page": 0,
        "pages": 0,
        "contacts": data
    }

@app.get(
    "/api/contact/{contact_id}/",
    response_model=ContactOut
)
def get_one_contact(contact_id: str):
    if offline:
        return {
            "_id": "k2i39i0r392ir8439",
            "name": "John Doe",
            "email": "etimitest@gmailcpom",
            "message": "Hello, I would like to know more about your products.",
            "phone_number": "+1234567890",
            "created_at": "2024-01-01"
        }
    contact_collection = database["contact_collection"]
    contact = contact_collection.find_one({"_id": ObjectId(contact_id)})
    # convert id to str
    contact["_id"] = str(contact["_id"])
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact

@app.delete(
    "/api/contact/{contact_id}/",
    status_code=status.HTTP_200_OK
)
def delete_contact(contact_id: str, token: str = Header()):
    if offline:
        return {"status": True}
    VALIDATE_TOKEN(token)
    contact_collection = database["contact_collection"]
    data = contact_collection.find_one({"_id": ObjectId(contact_id)})
    if data == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    contact_collection.delete_one(data)
    return {"status": True}