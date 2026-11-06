from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, field_validator

from config import constants
from metermind.api.access_control import issue_token
from metermind.api.password_hashing import hash_password, verify_password
from metermind.core.validators import validate_account_number, validate_email_address

router = APIRouter(tags=["accounts"])
accounts = {}


class AccountRequest(BaseModel):
    account_number: str
    email_address: str
    password: str
    role: str = constants.CONSUMER_ROLE

    @field_validator("account_number")
    @classmethod
    def account_number_is_well_formed(cls, given):
        text = str(given).strip()
        if not validate_account_number(text):
            raise ValueError(
                "account number must look like ACC followed by eight digits"
            )
        return text.upper()

    @field_validator("email_address")
    @classmethod
    def account_email_address_is_well_formed(cls, given):
        text = str(given).strip()
        if not validate_email_address(text):
            raise ValueError("email address must be a reachable mailbox address")
        return text.lower()


class AccountReply(BaseModel):
    account_number: str
    email_address: str
    role: str


class LoginRequest(BaseModel):
    account_number: str
    password: str


class TokenReply(BaseModel):
    access_token: str
    token_type: str
    role: str


@router.post(
    "/accounts",
    response_model=AccountReply,
    status_code=status.HTTP_201_CREATED,
)
def sign_up(wanted: AccountRequest):
    if wanted.account_number in accounts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="that account number is already signed up",
        )
    accounts[wanted.account_number] = {
        "account_number": wanted.account_number,
        "email_address": wanted.email_address,
        "hashed_password": hash_password(wanted.password),
        "role": wanted.role,
    }
    return AccountReply(
        account_number=wanted.account_number,
        email_address=wanted.email_address,
        role=wanted.role,
    )


@router.post("/accounts/login", response_model=TokenReply)
def log_in(wanted: LoginRequest):
    account_number = str(wanted.account_number).strip().upper()
    stored = accounts.get(account_number)
    if stored is None or not verify_password(wanted.password, stored["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="account number or password is wrong",
        )
    token = issue_token(account_number, stored["role"])
    return TokenReply(access_token=token, token_type="bearer", role=stored["role"])
