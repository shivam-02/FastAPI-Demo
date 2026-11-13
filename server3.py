from fastapi import FastAPI
from fastapi import Request
from fastapi import status
from fastapi import Depends
from pydantic import BaseModel,Field,model_validator
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from jose import JWTError
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import uvicorn
import asyncio

app=FastAPI()

crew = [
    {
        "id": 1,
        "name": "Cosmo", "role": "Captain", "experience": 10,
        "equipment": [
            {"name": "Helmet", "status": "Good"},
            {"name": "Suit", "status": "Needs Repair"}
        ]
    },
    {
        "id": 2,
        "name": "Alice", "role": "Engineer", "experience": 8,
        "equipment": [
            {"name": "Toolkit", "status": "Good"}
        ]
    },
]

users_db = {"user1": "pass1", "user2": "pass2"}

# Define the OAuth2 scheme to be used for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")



# Defining a Pydantic model for the crew member
class CrewMember(BaseModel):
    name: str
    role: str
    experience: int=Field(...,gt=0)
    equipment: list[Equipment]


    @model_validator(mode="after")
    def validate(cls, values):
        if values.role=='Captain' and values.experience<=5:
            raise ValueError("Captain must have more than 5 yrs of experience")
        return values

class Equipment(BaseModel):
    name: str
    status: str


def authenticate_user(username: str, password: str):
    # Check if user exists in the mock database
    if users_db.get(username) == password:
        return {"username": username}
    # Raise an HTTP 401 Unauthorized error if credentials are incorrect
    raise HTTPException(status_code=401, detail="Incorrect username or password")


@app.exception_handler(Exception)
async def general_exception_handler(request:Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail":"An unexpected error occurred,sorry for the inconvenience"}
    )


@app.middleware("http")
async def error_handling_middleware(request:Request, call_next):
    try:
        response=await call_next(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail":"An unexpected error occurred and we caught it with our middleware"}
        )
    return response

@app.get("/")
def read_root():
    return { "message" :"Welcome to the spaceship management system"}

@app.get("/crew")
async def read_crew():
    # Simulate a delay to mimic a time consuming task
    await asyncio.sleep(3)
    return {"crew":crew}

@app.get("/crew_path/{crew_id}",status_code=status.HTTP_200_OK)
def read_crew_member_by_path(crew_id:int,response_model=CrewMember):
    for member in crew:
        if member["id"]==crew_id:
            return member

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Crew member not found"
    )

@app.get("/crew_query/member")
def read_crew_member_by_query(crew_id: int):
    for member in crew:
        if member["id"] == crew_id:
            return member
    return {"message": "Crew member not found"}


@app.post("/crew", status_code=status.HTTP_201_CREATED)
async def add_crew_memeber(member:CrewMember):
    crew_id=max(member["id"] for member in crew)+1 if crew else 1
    new_member={"id":crew_id,"name":member.name,"role":member.role,"experience":member.experience,"equipment":member.equipment}
    crew.append(new_member)
    return {"crew_id":crew_id,"crew_member":new_member}

@app.put("/crew/{crew_id}")
async def update_crew_member(crew_id:int, request:Request):
    data= await request.json()
    name=data["name"]
    role=data["role"]

    for member in crew:
        if member["id"]==crew_id:
            member["name"]=name
            member["role"]=role
            return {"crew_id":crew_id,"crew_member":member}

    return {"message": "Crew member not found"}

@app.delete("/crew/{crew_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_crew_member(crew_id:int):
    # Find crew member and delete i
    for member in crew:
        if member["id"]==crew_id:
            crew.remove(member)
            return

    return {"message":"Crew member not found"}

# Configuration for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Token class
class Token(BaseModel):
    access_token: str
    token_type: str

# Function to create JWT token with an expiration time
def create_access_token(data: dict):
    # Copy the provided data to avoid modifying the original
    to_encode = data.copy()
    # Set the token expiration time
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Add the expiration time to the token payload
    to_encode.update({"exp": expire})
    # Encode the token with the secret key and algorithm
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Login endpoint
@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Check username and password in the database
    user = authenticate_user(form_data)
    # Create an access token
    access_token = create_access_token(data={"sub": user["username"]})
    # Return the access token 
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Decode and verify the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Extract the username from the token payload
        username: str = payload.get("sub")
        # Check if the username is present in the token payload
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        # Return the username if valid
        return {"username": username}
    # Handle any JWT decoding errors
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Secured endpoint which depends on decoding the token
@app.get("/secure-message")
async def read_secure_message(current_user: dict = Depends(get_current_user)):
    return {"message": "This is a secured message"}




if __name__=="__main__":
    uvicorn.run(app,host="127.0.0.1",port=8000)
