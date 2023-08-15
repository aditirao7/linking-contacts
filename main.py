from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models import SessionLocal, Contact
from sqlalchemy import or_
from datetime import datetime

app = FastAPI()

db = SessionLocal()


@ app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/identify")
async def identify(info: Request):
    req_info = await info.json()

    # Get request info
    email = req_info['email']
    phoneNumber = req_info['phoneNumber']

    # Insert contact
    newContact = Contact(**{'phoneNumber': phoneNumber, 'email': email, 'linkedId': None,
                            'linkPrecedence': 'primary', 'createdAt': datetime.now(), 'updatedAt': datetime.now()})
    db.add(newContact)
    db.commit()
    db.refresh(newContact)

    # Checking if primary matches given input
    primary = db.query(Contact).filter(or_(Contact.email == email, Contact.phoneNumber ==
                                           phoneNumber), Contact.linkPrecedence == 'primary').first()
    if primary is None:
        newContact.linkedId = primary.id
        newContact.linkPrecedence = 'secondary'
        newContact.updatedAt = datetime.now()
        db.add(newContact)
        db.commit()

    emailList = []
    phoneList = []
    secondaryContactIds = []

    # Return JSON response
    return JSONResponse({"contact": {"primaryContactId": None, "emails": emailList, "phoneNumbers": phoneList, "secondaryContactIds": secondaryContactIds}})
