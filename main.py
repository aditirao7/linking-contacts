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
        print(emailChainSize, phoneChainSize)

        # Both New: Insert as primary (CREATE)
        if emailChainSize == 0 and phoneChainSize == 0:
            print(1)
            newContact = Contact(**{'phoneNumber': phoneNumber, 'email': email, 'linkedId': None,
                                    'linkPrecedence': 'primary', 'createdAt': datetime.now(), 'updatedAt': datetime.now()})
            db.add(newContact)
            db.commit()
            db.refresh(newContact)
            emailList.append(email)
            phoneList.append(phoneNumber)
            primaryID = newContact.id
            primary = newContact

        # New Email: Insert and Link to chain with same phone number (CREATE)
        elif emailChainSize == 0 and phoneChainSize != 0:
            print(2)
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
        elif emailChainSize != 0 and phoneChainSize == 0:
            print(3)
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
            print(4)
            phonePrimary = phoneChain.filter(
                Contact.linkPrecedence == 'primary').first()
            if phonePrimary is None:
                phonePrimary = db.query(Contact).filter(
                    Contact.id == phoneChain.first().linkedId).first()
            emailPrimary = emailChain.filter(
                Contact.linkPrecedence == 'primary').first()
            if emailPrimary is None:
                emailPrimary = db.query(Contact).filter(
                    Contact.id == emailChain.first().linkedId).first()
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
            elif phonePrimary.id > emailPrimary.id:
                for contact in phoneChain:
                    contact.linkedId = emailPrimary.id
                    contact.updatedAt = datetime.now()
                    contact.linkPrecedence = 'secondary'
                    db.add(contact)
                db.commit()
                primary = emailPrimary
            else:
                primary = emailPrimary
            emailList.append(primary.email)
            phoneList.append(primary.phoneNumber)
            primaryID = primary.id

    # Seen Email/ Phone: Find all linked contacts and output (READ)
    else:
        primary = None
        if email:
            print(5)
            linked = db.query(Contact).filter(Contact.email == email)
            for contact in linked:
                if contact.linkPrecedence == 'primary':
                    primary = contact
                else:
                    primary = db.query(Contact).filter(
                        Contact.id == contact.linkedId).first()
                    break
        elif phoneNumber:
            print(6)
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
            print(7)
            return JSONResponse({"message": "Invalid Request!"})
        if primary:
            primaryID = primary.id

    # Populate output lists
    if primary:
        print(8)
        linked = db.query(Contact).filter(Contact.linkedId == primary.id)
        for contact in linked:
            if contact.email not in emailList:
                emailList.append(contact.email)
            if contact.phoneNumber not in phoneList:
                phoneList.append(contact.phoneNumber)
            secondaryContactIds.append(contact.id)

    # Return JSON response
    return JSONResponse({"contact": {"primaryContactId": primaryID, "emails": emailList, "phoneNumbers": phoneList, "secondaryContactIds": secondaryContactIds}})
