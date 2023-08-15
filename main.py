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

    emailList = []
    phoneList = []
    secondaryContactIds = []
    primaryID = None

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
            newContact = Contact(**{'phoneNumber': phoneNumber, 'email': email, 'linkedId': None,
                                    'linkPrecedence': 'primary', 'createdAt': datetime.now(), 'updatedAt': datetime.now()})
            db.add(newContact)
            db.commit()
            db.refresh(newContact)
            emailList.append(email)
            phoneList.append(phoneNumber)
            primaryID = newContact.id

        # New Email: Insert and Link to chain with same phone number (CREATE)
        if emailChainSize == 0 and phoneChainSize != 0:
            # Check if primary exists in chain
            primary = phoneChain.filter(
                Contact.linkPrecedence == 'primary').first()
            # Else get primary from linkedId
            if primary is None:
                primary = db.query(Contact).filter(
                    Contact.id == phoneChain.first().linkedId).first()
            # Insert
            newContact = Contact(**{'phoneNumber': phoneNumber, 'email': email, 'linkedId': primary.id,
                                    'linkPrecedence': 'secondary', 'createdAt': datetime.now(), 'updatedAt': datetime.now()})
            db.add(newContact)
            db.commit()
            db.refresh(newContact)
            emailList.append(primary.email)
            phoneList.append(primary.phoneNumber)
            primaryID = primary.id

        # New Phone: Insert and Link to chain with same email (CREATE)
        if emailChainSize != 0 and phoneChainSize == 0:
            # Check if primary exists in chain
            primary = emailChain.filter(
                Contact.linkPrecedence == 'primary').first()
            # Else get primary from linkedId
            if primary is None:
                primary = db.query(Contact).filter(
                    Contact.id == emailChain.first().linkedId).first()
            # Insert
            newContact = Contact(**{'phoneNumber': phoneNumber, 'email': email, 'linkedId': primary.id,
                                    'linkPrecedence': 'secondary', 'createdAt': datetime.now(), 'updatedAt': datetime.now()})
            db.add(newContact)
            db.commit()
            db.refresh(newContact)
            emailList.append(primary.email)
            phoneList.append(primary.phoneNumber)
            primaryID = primary.id

        # Both Seen: Email and phone chains need to be linked, one chain is changed to all secondary by comparing ID (UPDATE)
        else:
            phonePrimary = phoneChain.filter(
                Contact.linkPrecedence == 'primary').first()
            emailPrimary = emailChain.filter(
                Contact.linkPrecedence == 'primary').first()
            # Phone primary is actual primary
            if phonePrimary.id < emailPrimary.id:
                for contact in emailChain:
                    contact.linkedId = phonePrimary.id
                    contact.updatedAt = datetime.now()
                    contact.linkPrecedence = 'secondary'
                    db.add(contact)
                db.commit()
                primary = phonePrimary
            # Email primary is actual primary
            else:
                for contact in phoneChain:
                    contact.linkedId = emailPrimary.id
                    contact.updatedAt = datetime.now()
                    contact.linkPrecedence = 'secondary'
                    db.add(contact)
                db.commit()
                primary = emailPrimary
            emailList.append(primary.email)
            phoneList.append(primary.phoneNumber)
            primaryID = primary.id

    # Seen Email/ Phone: Find all linked contacts and output (READ)
    else:
        if email:
            linked = db.query(Contact).filter(Contact.email == email)
            for contact in linked:
                if contact.linkPrecedence == 'primary':
                    primary = contact
                else:
                    primary = db.query(Contact).filter(
                        Contact.id == contact.linkedId).first()
                    break
        elif phoneNumber:
            linked = db.query(Contact).filter(
                Contact.phoneNumber == phoneNumber)
            for contact in linked:
                if contact.linkPrecedence == 'primary':
                    primary = contact
                else:
                    primary = db.query(Contact).filter(
                        Contact.id == contact.linkedId).first()
                    break
        else:
            return JSONResponse({"message": "Invalid Request!"})

    # Populate output lists

    # Return JSON response
    return JSONResponse({"contact": {"primaryContactId": primaryID, "emails": emailList, "phoneNumbers": phoneList, "secondaryContactIds": secondaryContactIds}})
