from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
import jwt
import bcrypt
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="JWT Authentication API")

# Security settings (In production, move SECRET_KEY to a .env file)
SECRET_KEY = "your_super_secret_development_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database configuration mapping to your local Docker setup
DB_URL = "postgresql://tender_scrapping_agent:change-me-strong-password@localhost:5433/tender_scrapping_db"

def get_db_connection():
    """Creates a new database connection for each request."""
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def create_access_token(data: dict):
    """Generates a JWT token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Verifies user credentials against the database and returns a JWT token."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 1. Fetch user from the database
        cur.execute("SELECT username, hashed_password FROM users WHERE username = %s AND is_active = TRUE;", (form_data.username,))
        user = cur.fetchone()
        
        # 2. Check if user exists and verify the submitted password against the stored bcrypt hash
        if not user or not bcrypt.checkpw(form_data.password.encode('utf-8'), user['hashed_password'].encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 3. Generate token if credentials are valid
        access_token = create_access_token(data={"sub": user['username']})
        return {"access_token": access_token, "token_type": "bearer"}
        
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/")
async def root():
    return {"message": "JWT API is running. Go to /docs to test the login."}
    from fastapi.security import OAuth2PasswordBearer

# This tells FastAPI where clients should go to get their token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.get("/protected-tenders")
async def get_protected_tenders(token: str = Depends(oauth2_scheme)):
    """A secure endpoint that requires a valid JWT token to access."""
    return {
        "message": "If you are seeing this, you successfully passed the token!",
        "your_token": token
    }