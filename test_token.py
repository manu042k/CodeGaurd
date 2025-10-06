#!/usr/bin/env python3

from jose import jwt
from datetime import datetime, timedelta

# Settings from config
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"

# User ID from database
user_id = "f74b9e21-ec40-4729-bc88-eb640aa1205f"

# Create token
data = {"sub": user_id}
expires_delta = timedelta(minutes=60)  # 1 hour
expire = datetime.utcnow() + expires_delta
data.update({"exp": expire})

token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
print(f"JWT Token: {token}")
