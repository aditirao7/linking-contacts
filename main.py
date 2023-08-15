from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from models import SessionLocal, Contact
from sqlalchemy import or_, func
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
    email, phoneNumber = None, None
    keys = req_info.keys()
    if 'email' in keys:
        email = req_info['email']
    if 'phoneNumber' in keys:
        phoneNumber = req_info['phoneNumber']

    # Algorithm for linking
        # 6 types of valid input: Both New, Both Seen, New Email, New Phone, Seen Email with Null Phone, Seen Phone with Null Email
    if email and phoneNumber:
        # For checking
        emailChain = db.query(Contact).filter(Contact.email == email)
        phoneChain = db.query(Contact).filter(
            Contact.phoneNumber == phoneNumber)
        emailChainSize = emailChain.count()
        phoneChainSize = phoneChain.count()

        # Both New: Insert as primary (CREATE)
        if emailChainSize == 0 and phoneChainSize == 0:
            print(1)

        # New Email: Insert and Link to chain with same phone number (CREATE)
        if emailChainSize == 0 and phoneChainSize != 0:
            print(2)

        # New Phone: Insert and Link to chain with same email (CREATE)
        if emailChainSize != 0 and phoneChainSize == 0:
            print(3)

        # Both Seen: Email and phone chains need to be linked, one chain is changed to all secondary by comparing ID (UPDATE)
        else:
            print(4)

        # Insert contact only if either phone or email is new
        # newContact = Contact(**{'phoneNumber': phoneNumber, 'email': email, 'linkedId': None,
        #                        'linkPrecedence': 'primary', 'createdAt': datetime.now(), 'updatedAt': datetime.now()})
        # db.add(newContact)
        # db.commit()
        # db.refresh(newContact)

        # Checking if primary matches given input
        # primary = db.query(Contact).filter(or_(Contact.email == email, Contact.phoneNumber ==
        #                                       phoneNumber), Contact.linkPrecedence == 'primary').first()
        # if primary is None:
        #    newContact.linkedId = primary.id
        #    newContact.linkPrecedence = 'secondary'
        #    newContact.updatedAt = datetime.now()
        #    db.add(newContact)
        #    db.commit()

    else:
        # Seen Email/ Phone: Find all linked contacts and output (READ)
        print()

    emailList = []
    phoneList = []
    secondaryContactIds = []

    # Return JSON response
    return JSONResponse({"contact": {"primaryContactId": None, "emails": emailList, "phoneNumbers": phoneList, "secondaryContactIds": secondaryContactIds}})
