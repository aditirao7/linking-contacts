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


def addContact(phoneNumber, email, linkedId, linkPrecedence):
    time = datetime.now()
    contact = Contact(**{'phoneNumber': phoneNumber, 'email': email, 'linkedId': linkedId,
                         'linkPrecedence': linkPrecedence, 'createdAt': time, 'updatedAt': time})
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


def eitherPhoneOrEmailIsNew(chain, phoneNumber, email):
    # Check if primary exists in chain
    primary = chain.filter(
        Contact.linkPrecedence == 'primary').first()
    # Else get primary from linkedId
    if primary is None:
        primary = db.query(Contact).filter(
            Contact.id == chain.first().linkedId).first()
    # Insert
    addContact(phoneNumber, email, primary.id, 'secondary')
    return primary


def updateOutput(primary, emailList, phoneList, primaryID):
    emailList.append(primary.email)
    phoneList.append(primary.phoneNumber)
    primaryID = primary.id
    return emailList, phoneList, primaryID


def findPrimaryFromChain(chain):
    primary = chain.filter(
        Contact.linkPrecedence == 'primary').first()
    if primary is None:
        primary = db.query(Contact).filter(
            Contact.id == chain.first().linkedId).first()
    return primary


def findPrimaryFromLinked(linked):
    primary = None
    for contact in linked:
        if contact.linkPrecedence == 'primary':
            primary = contact
        else:
            primary = db.query(Contact).filter(
                Contact.id == contact.linkedId).first()
            break
    return primary


def updateChain(chain, primary):
    for contact in chain:
        contact.linkedId = primary.id
        contact.updatedAt = datetime.now()
        contact.linkPrecedence = 'secondary'
        db.add(contact)
    db.commit()
    return primary


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

    # Output variables
    emailList = []
    phoneList = []
    secondaryContactIds = []
    primaryID = None

    primary = None

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
            primary = addContact(phoneNumber, email, None, 'primary')

        # New Email: Insert and Link to chain with same phone number (CREATE)
        elif emailChainSize == 0 and phoneChainSize != 0:
            primary = eitherPhoneOrEmailIsNew(phoneChain, phoneNumber, email)

        # New Phone: Insert and Link to chain with same email (CREATE)
        elif emailChainSize != 0 and phoneChainSize == 0:
            primary = eitherPhoneOrEmailIsNew(emailChain, phoneNumber, email)

        # Both Seen: Email and phone chains need to be linked, one chain is changed to all secondary by comparing ID (UPDATE)
        else:
            phonePrimary = findPrimaryFromChain(phoneChain)
            emailPrimary = findPrimaryFromChain(emailChain)
            # Phone primary is actual primary
            if phonePrimary.id < emailPrimary.id:
                primary = updateChain(emailChain, phonePrimary)
            # Email primary is actual primary
            elif phonePrimary.id > emailPrimary.id:
                primary = updateChain(phoneChain, emailPrimary)
            else:
                primary = emailPrimary

    # Seen Email/ Phone: Find all linked contacts and output (READ)
    else:
        if email:
            linked = db.query(Contact).filter(Contact.email == email)
            primary = findPrimaryFromLinked(linked)
        elif phoneNumber:
            linked = db.query(Contact).filter(
                Contact.phoneNumber == phoneNumber)
            primary = findPrimaryFromLinked(linked)
        else:
            return JSONResponse({"message": "Invalid Request!"})

    # Populate output lists
    if primary:
        emailList, phoneList, primaryID = updateOutput(
            primary, emailList, phoneList, primaryID)
        linked = db.query(Contact).filter(Contact.linkedId == primary.id)
        for contact in linked:
            if contact.email not in emailList:
                emailList.append(contact.email)
            if contact.phoneNumber not in phoneList:
                phoneList.append(contact.phoneNumber)
            secondaryContactIds.append(contact.id)

    # Return JSON response
    return JSONResponse({"contact": {"primaryContactId": primaryID, "emails": emailList, "phoneNumbers": phoneList, "secondaryContactIds": secondaryContactIds}})
