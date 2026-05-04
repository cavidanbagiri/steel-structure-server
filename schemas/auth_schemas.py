


from pydantic import BaseModel, EmailStr


class UserRegisterSchema(BaseModel):

    firstname: str
    lastname: str
    username: str
    email: EmailStr()
    password: str
    status: str



class UserLoginSchema(BaseModel):

    email: EmailStr()
    password: str
