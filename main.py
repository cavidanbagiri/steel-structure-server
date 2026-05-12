
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import auth_router
from routers import transport_router
from routers import main_data_router
from routers import erected_router
from routers import combine_router

app = FastAPI()


load_dotenv()


origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(router = auth_router.router, prefix="/api/auth", tags=["User"])
app.include_router(router = main_data_router.router, prefix="/api/main", tags=["Main"])
app.include_router(router = transport_router.router, prefix="/api/transport", tags=["Transport"])
app.include_router(router = erected_router.router, prefix="/api/erected", tags=["Erected"])
app.include_router(router = combine_router.router, prefix="/api/combine", tags=["Combine"])
