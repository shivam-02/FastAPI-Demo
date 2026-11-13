from fastapi import FastAPI
from fastapi import Request
from pydantic import BaseModel,Field,model_validator

import uvicorn
import asyncio

app=FastAPI()

crew = [
    {"id": 1, "name": "Cosmo", "role": "Captain", "experience": 10},
    {"id": 2, "name": "Alice", "role": "Engineer", "experience": 8},
    {"id": 3, "name": "Bob", "role": "Scientist", "experience": 5}
]


# Defining a Pydantic model for the crew member
class CrewMember(BaseModel):
    name: str
    role: str
    experience: int=Field(...,gt=0)


    @model_validator(mode="after")
    def validate(cls, values):
        if values.role=='Captain' and values.experience<=5:
            raise ValueError("Captain must have more than 5 yrs of experience")
        return values

@app.get("/")
def read_root():
    return { "message" :"Welcome to the spaceship management system"}

@app.get("/crew")
async def read_crew():
    # Simulate a delay to mimic a time consuming task
    await asyncio.sleep(3)
    return {"crew":crew}

@app.get("/crew_path/{crew_id}")
def read_crew_member_by_path(crew_id:int,response_model=CrewMember):
    for member in crew:
        if member["id"]==crew_id:
            return member

    return {"message":"Crew member not found"}

@app.get("/crew_query/member")
def read_crew_member_by_query(crew_id: int):
    for member in crew:
        if member["id"] == crew_id:
            return member
    return {"message": "Crew member not found"}


@app.post("/crew")
async def add_crew_memeber(member:CrewMember):
    crew_id=max(member["id"] for member in crew)+1 if crew else 1
    new_member={"id":crew_id,"name":member.name,"role":member.role,"experience":member.experience}
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

@app.delete("/crew/{crew_id}")
async def delete_crew_member(crew_id:int):
    # Find crew member and delete i
    for member in crew:
        if member["id"]==crew_id:
            crew.remove(member)
            return {"message":"Crew member removed"}

    return {"message":"Crew member not found"}




if __name__=="__main__":
    uvicorn.run(app,host="127.0.0.1",port=8000)
