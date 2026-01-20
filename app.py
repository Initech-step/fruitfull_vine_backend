from fastapi import (
    FastAPI,
    HTTPException,
    status,
    Request,
    Response,
    Header,
    UploadFile,
    Form,
    File,
)
from fastapi.middleware.cors import CORSMiddleware
from bson.objectid import ObjectId
from typing import List, Optional
import math
from datetime import datetime
from utils.database import connect_to_db
from utils.file_upload import upload_file_to_s3, upload_file_to_cloudinary
from utils.models import (
    LogInDetails,
    Category,
    CategoryOut,
    BlogPostOut,
    BlogPostOutMultiple,
    ProductOut,
    ProductMultiple,
    EmailNewsletter,
    ContactUs,
    ContactOut,
    ContactMultiple,
    CategoryType,
)
import os


def str_to_bool(s):
    s = s.strip().lower()  # Remove leading/trailing spaces and convert to lowercase
    if s == "true":
        return True
    elif s == "false":
        return False
    else:
        # Handle invalid input as needed (e.g., raise a ValueError)
        raise ValueError(f"Invalid boolean string: '{s}'")


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
offline = str_to_bool(os.getenv("OFFLINE_MODE", False))
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


@app.post("/api/category/", status_code=status.HTTP_201_CREATED, response_model=dict)
def create_category(category: Category, token: str = Header()):
    if offline:
        print("Offline mode: skipping category creation")
        return {"status": True}

    if VALIDATE_TOKEN(token):
        category_data = category.model_dump()
        category_collection = database["categories_collection"]
        try:
            category_collection.insert_one(category_data)
            return {"status": True}
        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create catgory",
            )


@app.get("/api/category/", response_model=List[CategoryOut])
def get_categories(type: Optional[CategoryType] = None):
    if offline:
        return [
            {
                "_id": "64b8f4f2f2f2f2f2f2f2f2f2",
                "name": "Sample Category",
                "type": "Cat/prod",
                "description": "This is a sample category description.",
            },
            {
                "_id": "ofiolnbkcr",
                "name": "Sample Category 2",
                "type": "Cat/prod",
                "description": "This is a sample category description.",
            },
            {
                "_id": "k2i39i0r392ir8439",
                "name": "Sample Category 3",
                "type": "Cat/prod",
                "description": "This is a sample category description.",
            },
        ]
    category_collection = database["categories_collection"]
    if type is not None:
        data = list(category_collection.find({"type": type.value}))
    else:
        data = list(category_collection.find({}))
    for d in data:
        d["_id"] = str(d["_id"])
    return data


@app.delete(
    "/api/category/{c_id}/{type}/", status_code=status.HTTP_200_OK, response_model=dict
)
def delete_category(
    c_id: str, type: CategoryType = CategoryType.product, token: str = Header()
):
    if offline:
        return {"status": True}

    if VALIDATE_TOKEN(token):
        # find and verify category
        category_collection = database["categories_collection"]
        category_data = category_collection.find_one({"_id": ObjectId(c_id)})
        if category_data == None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
            )
        # check if linked to any products or blog posts
        if type == CategoryType.product:
            product_collection = database["products_collection"]
            if product_collection.find_one({"category_id": ObjectId(c_id)}) is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category is linked to a product",
                )
            else:
                category_collection.delete_one({"_id": ObjectId(c_id)})

        if type == CategoryType.blog:
            # get the needed collections
            blog_posts_collection = database["blog_posts_collection"]
            if (
                blog_posts_collection.find_one({"category_id": ObjectId(c_id)})
                is not None
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Category is linked to a blog post",
                )
            else:
                category_collection.delete_one({"_id": ObjectId(c_id)})

        return {"status": True}


@app.put("/api/category/{c_id}/", status_code=status.HTTP_200_OK, response_model=dict)
def update_category(c_id: str, category: Category, token: str = Header()):
    if offline:
        return {"status": True}
    VALIDATE_TOKEN(token)

    category_data = category.model_dump()
    category_collection = database["blog_categories_collection"]
    data_target = category_collection.find_one({"_id": ObjectId(c_id)})
    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
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


@app.post("/api/blog/", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_blog_cloudinary(
    token: str = Header(),
    category_id: str = Form(...),
    category_name: str = Form(...),
    post_title: str = Form(...),
    short_title: str = Form(...),
    body: str = Form(...),
    image: Optional[UploadFile] = File(None),
    draft: bool = Form(False),
):
    if offline:
        return {"status": True}
    VALIDATE_TOKEN(token)

    # 1. Read file content
    if image is not None:
        file_content = await image.read()
        # 2. Upload using utility
        upload_file = upload_file_to_cloudinary(file_content)

        # 3. Create the document for MongoDB
        blog_data = {
            "url": upload_file["url"],
            "secure_url": upload_file["secure_url"],
            "public_id": upload_file["public_id"],
            "post_title": post_title,
            "body": body,
            "category_id": category_id,
            "category_name": category_name,
            "short_title": short_title,
            "draft": draft,
            "date": str(datetime.now()),
        }
    else:
        blog_data = {
            "post_title": post_title,
            "body": body,
            "category_id": category_id,
            "category_name": category_name,
            "short_title": short_title,
            "draft": draft,
            "date": str(datetime.now()),
        }

    blog_collection = database["blog_posts_collection"]
    blog_collection.insert_one(blog_data)

    return {"status": True}


@app.put(
    "/api/blog/{b_id}/", status_code=status.HTTP_200_OK, response_model=BlogPostOut
)
def edit_blog_content(
    b_id: str,
    category_id: Optional[str] = Form(None),
    category_name: Optional[str] = Form(None),
    post_title: Optional[str] = Form(None),
    short_title: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    token: str = Header(),
):
    if offline:
        return {
            "_id": "k2i39i0r392ir8439",
            "url": "https://example.com/image.jpg",
            "secure_url": "https://example.com/image.jpg",
            "public_id": "HXC0-DWHDE",
            "post_title": "Sample Post Title",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_title": "Sample Short Title",
            "body": "Sample blog post body content.",
        }

    VALIDATE_TOKEN(token)

    blog_collection = database["blog_posts_collection"]
    # 2. Build the update dictionary dynamically
    # Only include fields that are not None
    update_data = {}

    fields = {
        "category_id": category_id,
        "category_name": category_name,
        "post_title": post_title,
        "short_title": short_title,
        "body": body,
    }

    if image is not None:
        file_content = image.read()
        upload_file = upload_file_to_cloudinary(file_content)
        update_data["url"] = upload_file["url"]
        update_data["secure_url"] = upload_file["secure_url"]
        update_data["public_id"] = upload_file["public_id"]

    for key, value in fields.items():
        if value is not None:
            update_data[key] = value

    data_target = blog_collection.find_one({"_id": ObjectId(b_id)})

    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    blog_collection.update_one(
        {"_id": ObjectId(b_id)},
        {"$set": update_data},
    )
    data_output = blog_collection.find_one({"_id": ObjectId(b_id)})
    data_output["_id"] = str(data_output["_id"])
    return data_output


# GET ALL BLOG CONTENTS
@app.get(
    "/api/blog/",
    response_model=BlogPostOutMultiple,
)
def get_blog_posts(page: int = 1, limit: int = 15, category_id: Optional[str] = None):
    if offline:
        return {
            "blogs": [
                {
                    "_id": "k2i39i0r392ir8439",
                    "url": "https://example.com/image.jpg",
                    "secure_url": "https://example.com/image.jpg",
                    "public_id": "HXC0-DWHDE",
                    "post_title": "Sample Post Title",
                    "category_name": "Sample Category",
                    "category_id": "sample_category_id",
                    "short_title": "Sample Short Title",
                    "body": "Sample blog post body content.",
                },
                {
                    "_id": "oi23j4oij234oij234",
                    "url": "https://example.com/image.jpg",
                    "secure_url": "https://example.com/image.jpg",
                    "public_id": "HXC0-DWHDE",
                    "post_title": "Another Sample Post Title",
                    "category_name": "Another Sample Category",
                    "category_id": "another_sample_category_id",
                    "short_title": "Another Sample Short Title",
                    "body": "Another sample blog post body content.",
                },
            ],
            "pages": 1,
            "current_page": 1,
        }
    blog_collection = database["blog_posts_collection"]
    # guardrails
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit
    total_docs = blog_collection.count_documents({})
    total_pages = math.ceil(total_docs / limit)

    cursor = blog_collection.find({}).sort("_id", -1).skip(skip).limit(limit)
    if category_id is not None:
        cursor = (
            blog_collection.find({"category_id": category_id}).skip(skip).limit(limit)
        )

    blogs = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        blogs.append(doc)

    return {"blogs": blogs, "pages": total_pages, "current_page": page}


# GET SPECIFIC BLOG POST
@app.get(
    "/api/blog/{b_id}/", status_code=status.HTTP_200_OK, response_model=BlogPostOut
)
def get_blog_content(b_id: str):
    if offline:
        return {
            "_id": "k2i39i0r392ir8439",
            "url": "https://example.com/image.jpg",
            "secure_url": "https://example.com/image.jpg",
            "public_id": "HXC0-DWHDE",
            "post_title": "Sample Post Title",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_title": "Sample Short Title",
            "body": "Sample blog post body content.",
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
@app.delete("/api/blog/{b_id}/", status_code=status.HTTP_200_OK)
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
@app.get("/api/get_last_post/", response_model=BlogPostOut)
def get_last_post():
    if offline:
        return {
            "_id": "k2i39i0r392ir8439",
            "url": "https://example.com/image.jpg",
            "secure_url": "https://example.com/image.jpg",
            "public_id": "HXC0-DWHDE",
            "post_title": "Sample Post Title",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_title": "Sample Short Title",
            "body": "Sample blog post body content.",
        }
    blog_collection = database["blog_posts_collection"]
    last_post = blog_collection.find_one({}, sort=[("_id", -1)])

    if not last_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No blog posts found"
        )

    last_post["_id"] = str(last_post["_id"])
    return last_post


"""
PRODUCTS
"""


@app.post("/api/product/", status_code=status.HTTP_201_CREATED, response_model=dict)
async def create_product(
    category_id: str = Form(...),
    category_name: str = Form(...),
    product_name: str = Form(...),
    short_description: str = Form(...),
    body: str = Form(...),
    draft: bool = Form(False),
    images: List[UploadFile] = File([]),
    token: str = Header(),
):
    if offline:
        return {"status": True, "offline": True}
    VALIDATE_TOKEN(token)

    uploaded_images = []

    for image in images:
        file_content = await image.read()
        upload_file = upload_file_to_cloudinary(file_content)
        upload_file_data = {
            "url": upload_file["url"],
            "secure_url": upload_file["secure_url"],
            "public_id": upload_file["public_id"],
        }
        uploaded_images.append(upload_file_data)

    product_data = {
        "images": uploaded_images,
        "product_name": product_name,
        "body": body,
        "category_id": category_id,
        "category_name": category_name,
        "short_description": short_description,
        "draft": draft,
        "date": str(datetime.now().today()),
    }
    product_collection = database["products_collection"]
    product_collection.insert_one(product_data)

    return {"status": True}


@app.get(
    "/api/products/",
    response_model=ProductMultiple,
)
def get_products(page: int = 1, limit: int = 15, category_id: Optional[str] = None):
    if offline:
        return {
            "products": [
                {
                    "_id": "k2i39i0r392ir8439",
                    "images": [
                        {
                            "url": "https://example.com/image.jpg",
                            "secure_url": "https://example.com/image.jpg",
                            "public_id": "HXC0-DWHDE"
                        }
                    ],
                    "product_name": "Sample Product Name",
                    "category_name": "Sample Category",
                    "category_id": "sample_category_id",
                    "short_description": "Sample short description of the product.",
                    "body": "Detailed description of the sample product.",
                    "iframe": "<iframe src='https://example.com'></iframe>",
                },
                {
                    "_id": "oi23j4oij234oij234",
                    "images": [
                        {
                            "url": "https://example.com/image.jpg",
                            "secure_url": "https://example.com/image.jpg",
                            "public_id": "HXC0-DWHDE"
                        }
                    ],
                    "product_name": "Another Sample Product Name",
                    "category_name": "Another Sample Category",
                    "category_id": "another_sample_category_id",
                    "short_description": "Another sample short description of the product.",
                    "body": "Detailed description of another sample product.",
                },
            ],
            "pages": 1,
            "current_page": 1,
        }

    product_collection = database["products_collection"]

    # guardrails
    page = max(page, 1)
    limit = min(max(limit, 1), 50)
    skip = (page - 1) * limit

    total_docs = product_collection.count_documents({})
    total_pages = math.ceil(total_docs / limit)

    cursor = product_collection.find({}).sort("_id", -1).skip(skip).limit(limit)
    print(cursor)
    if category_id is not None:
        cursor = (
            product_collection.find({"category_id": category_id})
            .sort("_id", -1)
            .skip(skip)
            .limit(limit)
        )

    products = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        products.append(doc)
        print(doc)

    return {"products": products, "pages": total_pages, "current_page": page}


@app.get(
    "/api/product/{p_id}/", 
    status_code=status.HTTP_200_OK, 
    response_model=ProductOut
)
def get_product(p_id: str):
    if offline:
        return {
            "_id": "k2i39i0r392irrr8439",
            "images": [
                {
                    "url": "https://example.com/image.jpg",
                    "secure_url": "https://example.com/image.jpg",
                    "public_id": "HXC0-DWHDE"
                }
            ],
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


@app.get("/api/get_last_product/", response_model=ProductOut)
def get_last_product():
    if offline:
        return {
            "_id": "k2i39i0r392irrr8439",
            "images": [
                {
                    "url": "https://example.com/image.jpg",
                    "secure_url": "https://example.com/image.jpg",
                    "public_id": "HXC0-DWHDE"
                }
            ],
            "product_name": "Sample Product Name",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_description": "Sample short description of the product.",
            "body": "Detailed description of the sample product.",
            "iframe": "<iframe src='https://example.com'></iframe>",
        }
    product_collection = database["products_collection"]
    last_post = product_collection.find_one({}, sort=[("_id", -1)])

    if not last_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No blog posts found"
        )

    last_post["_id"] = str(last_post["_id"])
    return last_post


@app.delete("/api/product/{p_id}/", status_code=status.HTTP_200_OK)
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
    "/api/edit_product/{p_id}",
    status_code=status.HTTP_200_OK,
    response_model=ProductOut,
)
def edit_product(
    p_id: str,
    product_name: Optional[str] = Form(None),
    short_description: Optional[str] = Form(None),
    body: Optional[str] = Form(None),
    draft: Optional[bool] = Form(False),
    images: List[UploadFile] = File([]),
    token: str = Header(),
):
    if offline:
        return {
            "_id": "k2i39i0r392irrr8439",
            "images": [
                {
                    "url": "https://example.com/image.jpg",
                    "secure_url": "https://example.com/image.jpg",
                    "public_id": "HXC0-DWHDE"
                }
            ],
            "product_name": "Sample Product Name",
            "category_name": "Sample Category",
            "category_id": "sample_category_id",
            "short_description": "Sample short description of the product.",
            "body": "Detailed description of the sample product.",
            "iframe": "<iframe src='https://example.com'></iframe>",
        }
    VALIDATE_TOKEN(token)

    product_collection = database["products_collection"]
    # 2. Build the update dictionary dynamically
    # Only include fields that are not None
    update_data = {}
    update_images = []

    fields = {
        "product_name": product_name,
        "short_description": short_description,
        "body": body,
        "draft": draft,
        "images": update_images,
    }

    for image in images:
        file_content = image.read()
        upload_file = upload_file_to_cloudinary(file_content)
        update_images.append(
            {
                "url": upload_file["url"],
                "secure_url": upload_file["secure_url"],
                "public_id": upload_file["public_id"],
            }
        )

    for key, value in fields.items():
        if value is not None:
            update_data[key] = value

    data_target = product_collection.find_one({"_id": ObjectId(p_id)})

    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )

    product_collection.update_one(
        {"_id": ObjectId(p_id)},
        {"$set": update_data},
    )
    data_output = product_collection.find_one({"_id": ObjectId(p_id)})
    data_output["_id"] = str(data_output["_id"])
    return data_output


"""
CONTACT US
"""


@app.post("/api/contact/", status_code=201, response_model=dict)
def create_contact(contact: ContactUs):
    if offline:
        return {"status": True}
    data = contact.model_dump()
    contact_collection = database["contact_collection"]
    contact_collection.insert_one(data)
    return {"status": True}


@app.get("/api/contact/", response_model=ContactMultiple)
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
                    "created_at": "2024-01-01",
                },
                {
                    "_id": "k2jwesccmsi39i0r392ir8439",
                    "name": "John Rugged",
                    "email": "etimitest@gmailcpom",
                    "message": "Hello, I would like to know more about your products.",
                    "phone_number": "+1234567890",
                    "created_at": "2024-01-01",
                },
            ],
        }

    contact_collection = database["contact_collection"]
    data = list(contact_collection.find({}).sort("created_at", -1))
    for d in data:
        d["_id"] = str(d["_id"])
    return {"current_page": 0, "pages": 0, "contacts": data}


@app.get("/api/contact/{contact_id}/", response_model=ContactOut)
def get_one_contact(contact_id: str):
    if offline:
        return {
            "_id": "k2i39i0r392ir8439",
            "name": "John Doe",
            "email": "etimitest@gmailcpom",
            "message": "Hello, I would like to know more about your products.",
            "phone_number": "+1234567890",
            "created_at": "2024-01-01",
        }
    contact_collection = database["contact_collection"]
    contact = contact_collection.find_one({"_id": ObjectId(contact_id)})
    # convert id to str
    contact["_id"] = str(contact["_id"])
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    return contact


@app.delete("/api/contact/{contact_id}/", status_code=status.HTTP_200_OK)
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
