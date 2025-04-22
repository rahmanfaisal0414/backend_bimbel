# accounts/utils.py
import random
import string

def generate_simple_token(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
