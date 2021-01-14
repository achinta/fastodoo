from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import AuthenticationBackend, AuthenticationError, AuthCredentials, UnauthenticatedUser
from starlette.authentication import SimpleUser
from starlette.requests import HTTPConnection
import typing
from typing import List
import jwt

import os

# simpler logging
import logging
from loguru import logger
logging.basicConfig(level=logging.INFO)

class FastOdooUser(SimpleUser):
    def __init__(self, username: str, user_id: int, partner_id: int, scopes=List[str]) -> None:
        super().__init__(username)
        self.user_id = user_id
        self.partner_id = partner_id
        self.scopes = scopes

class JWTAuthBackend(AuthenticationBackend):
    '''
    Authenticate with JWT using the public key configured
    '''
    def __init__(self) -> None:
        super().__init__()
        self.jwt_pub_path = os.environ.get('JWT_PUB_PATH')
        self.jwt_pub_key = open(self.jwt_pub_path).read()

    async def authenticate(self, conn: HTTPConnection) -> typing.Optional[typing.Tuple["AuthCredentials", "BaseUser"]]:
        if 'Authorization' not in conn.headers:
            logger.info("'Authorization' not found in Headers")
            return (AuthCredentials(), UnauthenticatedUser)

        if not self.jwt_pub_path:
            raise AuthenticationError('JWT Public key not configured')

        auth = conn.headers['Authorization']
        try:
            decoded = jwt.decode(auth, self.jwt_pub_key, algorithms=["RS512"])
            logger.info("Valid JWT token.")
            logger.info(f"User id is {decoded.get('user_id')}")
            scopes = decoded['scope'].split() if decoded.get('scope').split() else []

            user = FastOdooUser(username='', user_id=decoded.get('user_id'), 
                partner_id=decoded.get('partner_id'), scopes=scopes)
            return (AuthCredentials(scopes), user)

        except:
            raise AuthenticationError('Could not decode JWT')


# class JWTMiddleware:
#     def __init__(self, app: ASGIApp, minimum_size: int = 500) -> None:
#         self.app = app
#         JWT_PUB_PATH = os.getenv('JWT_PUB_PATH')
#         if not JWT_PUB_PATH:
#             logging.error('Environement Variable JWT_PUB_PATH not found')

#     async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        
#         await self.app(scope, receive, send)