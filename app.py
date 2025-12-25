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
    ImageModel,
    ImageGroup,
    BlogPost,
    Admin,
    PageContent,
    EmailNewsletter,
)

# initialize app
app = FastAPI()

"""SET UP CORS"""
origins = ["http://localhost:5173", "https://fyapurplegirls.org"]
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
    response_model=CategoryOut
)
def get_categories():
    category_collection = database['blog_categories_collection']
    data = list(category_collection.find({}))
    for d in data:
        d["_id"] = str(d["_id"])
    return CategoryOut(
        data=data,
        status=True,
        no_of_pages=0,
        current_page=0
    )


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
    if VALIDATE_TOKEN(token):
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


@app.post("/api/add_post/", status_code=status.HTTP_201_CREATED)
def add_blog_post(blog: BlogPost, token: str = Header()):
    if VALIDATE_TOKEN(token):
        blog_data = blog.model_dump()
        blog_collection = database.BlogPost
        try:
            blog_collection.insert_one(blog_data)
            return {"status": True}
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add blog post",
            )


# API FOR EDIT BLOG POST
@app.post("/api/edit_blog_content/{b_id}", status_code=status.HTTP_200_OK)
def edit_blog_content(blog_content: BlogPost, b_id: str, token: str = Header()):
    if VALIDATE_TOKEN(token):
        blog_data = blog_content.model_dump()
        blog_collection = database.BlogPost
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
                    "video": blog_data.get("video"),
                    "iframe": blog_data.get("iframe"),
                }
            },
        )
        return {"status": True}


# GET SPECIFIC BLOG POST
@app.get("/api/get_blog_content/{b_id}", status_code=status.HTTP_200_OK)
def get_blog_content(b_id: str):
    blog_collection = database.BlogPost
    data_target = blog_collection.find_one({"_id": ObjectId(b_id)})
    if data_target == None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
        )
    ok_data = {
        "id": str(data_target.get("_id")),
        "image_url": str(data_target.get("image_url")),
        "post_title": str(data_target.get("post_title")),
        "category_name": str(data_target.get("category_name")),
        "category_id": str(data_target.get("category_id")),
        "short_title": str(data_target.get("short_title")),
        "body": str(data_target.get("body")),
        "date": str(data_target.get("date")),
        "video": str(data_target.get("video")),
        "iframe": str(data_target.get("iframe")),
    }
    return {"status": True, "content": ok_data}


# GET ALL BLOG CONTENTS
@app.get("/api/get_blog_posts/")
def get_blog_posts(page: int = 1, limit: int = 9):
    blog_collection = database.BlogPost
    data = list(blog_collection.find({}))
    data.reverse()

    number_of_pages = math.ceil(len(data) / limit)
    serialized_data = []
    pages = []

    for num in range(1, number_of_pages + 1):
        pages.append(num)
        for i in range(limit):
            # check if the list is empty
            if data != []:
                # select the next item on the list
                blog_item = data[0]
                serialized_data.append(
                    {
                        "id": str(blog_item.get("_id")),
                        "post_title": str(blog_item.get("post_title")),
                        "category_name": str(blog_item.get("category_name")),
                        "image_url": str(blog_item.get("image_url")),
                        "category_id": str(blog_item.get("category_id")),
                        "body": str(blog_item.get("body")),
                        "date": str(blog_item.get("date")),
                        "short_title": str(blog_item.get("short_title")),
                        # add a property of page number to the
                        "page_no": num,
                    }
                )
                # delete blog item from data
                del data[0]
            else:
                break
    return {"status": True, "blogs": serialized_data, "pages": pages}


# GET BLOG POSTS BY CATEGORY
@app.get("/api/get_posts_by_category/")
def get_blog_posts(category_id: str, limit: int = 9):
    blog_collection = database.BlogPost
    data = list(blog_collection.find({"category_id": str(category_id)}))
    data.reverse()

    number_of_pages = math.ceil(len(data) / limit)
    serialized_data = []
    pages = []

    for num in range(1, number_of_pages + 1):
        pages.append(num)
        for i in range(limit):
            # check if the list is empty
            if data != []:
                # select the next item on the list
                blog_item = data[0]
                serialized_data.append(
                    {
                        "id": str(blog_item.get("_id")),
                        "post_title": str(blog_item.get("post_title")),
                        "category_name": str(blog_item.get("category_name")),
                        "image_url": str(blog_item.get("image_url")),
                        "category_id": str(blog_item.get("category_id")),
                        "body": str(blog_item.get("body")),
                        "date": str(blog_item.get("date")),
                        "short_title": str(blog_item.get("short_title")),
                        # add a property of page number to the
                        "page_no": num,
                    }
                )
                # delete blog item from data
                del data[0]
            else:
                break
    return {"status": True, "blogs": serialized_data, "pages": pages}


# DELETE blog CONTENT
@app.delete("/api/del_blog_post/{b_id}/", status_code=status.HTTP_200_OK)
def delete_blog_post(b_id: str, token: str = Header()):
    if VALIDATE_TOKEN(token):
        blog_collection = database.BlogPost
        data = blog_collection.find_one({"_id": ObjectId(b_id)})
        if data == None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found"
            )
        blog_collection.delete_one(data)
        return {"status": True}


# GET LAST BLOG POST
@app.get("/api/get_last_post/")
def get_last_post():
    blog_collection = database.BlogPost
    # get last item in blog
    all = list(blog_collection.find({}))
    last_post = all[-1]
    # get data for serialization
    serialized_data = {
        "id": str(last_post.get("_id")),
        "post_title": str(last_post.get("post_title")),
        "category_name": str(last_post.get("category_name")),
        "image_url": str(last_post.get("image_url")),
        "category_id": str(last_post.get("category_id")),
        "body": str(last_post.get("body")),
        "date": str(last_post.get("date")),
        "short_title": str(last_post.get("short_title")),
        "iframe": str(last_post.get("iframe")),
        "video": str(last_post.get("video")),
    }
    return {"status": True, "data": serialized_data}


# GET LAST 3 POSTS
@app.get("/api/get_recent_posts/")
def get_blog_posts():
    blog_collection = database.BlogPost
    # get last item in blog
    all = list(blog_collection.find({}))
    serialized_data = []
    if len(all) > 3:
        recent_posts = all[-3:]
        # get data for serialization
        for d in recent_posts:
            serialized_data.append(
                {
                    "id": str(d.get("_id")),
                    "post_title": str(d.get("post_title")),
                    "category_name": str(d.get("category_name")),
                    "image_url": str(d.get("image_url")),
                    "category_id": str(d.get("category_id")),
                    "body": str(d.get("body")),
                    "date": str(d.get("date")),
                    "short_title": str(d.get("short_title")),
                }
            )
        serialized_data.reverse()
        return {"status": True, "blogs": serialized_data}
    else:
        for d in all:
            serialized_data.append(
                {
                    "id": str(d.get("_id")),
                    "post_title": str(d.get("post_title")),
                    "category_name": str(d.get("category_name")),
                    "image_url": str(d.get("image_url")),
                    "category_id": str(d.get("category_id")),
                    "body": str(d.get("body")),
                    "date": str(d.get("date")),
                    "short_title": str(d.get("short_title")),
                }
            )
            serialized_data.reverse()
        return {"status": True, "blogs": serialized_data}




