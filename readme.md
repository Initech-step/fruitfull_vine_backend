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
