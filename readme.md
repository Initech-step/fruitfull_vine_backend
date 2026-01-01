# THE BACKEND FOR THE FRUITFULL VINE BUSINESS SITE

to run black
# in app dir activate venv
>> black .

to run tests
>> python -m pytest -s

to run category tests
>> python -m pytest tests/test_category.py -s

to run products test
>> python -m pytest tests/test_product.py -s

to run blog tests
>> python -m pytest tests/test_blog.py -s

to run contact tests
>> python -m pytest tests/test_contact.py -s

# APIS

GET http://127.0.0.1:8000/api/category/
POST http://127.0.0.1:8000/api/category/
DELETE http://127.0.0.1:8000/api/category/

GET http://127.0.0.1:8000/api/products/
POST http://127.0.0.1:8000/api/products/
DELETE http://127.0.0.1:8000/api/products/

GET http://127.0.0.1:8000/api/blog/
POST http://127.0.0.1:8000/api/blog/
DELETE http://127.0.0.1:8000/api/blog/
