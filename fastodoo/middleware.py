from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import AuthenticationBackend, AuthenticationError, AuthCredentials, UnauthenticatedUser
from starlette.authentication import SimpleUser
from starlette.requests import HTTPConnection
import typing
from typing import List
import jwt

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

import os

# simpler logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class FastOdooUser(SimpleUser):
    def __init__(self, username: str, user_id: int, partner_id: int, scopes=List[str]) -> None:
        super().__init__(username)
        self.user_id = user_id
        self.partner_id = partner_id
        self.scopes = scopes

def create_keys():
    '''generate private and public keys'''
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Get the public key
    public_key = private_key.public_key()

    # Serialize the private key to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize the public key to PEM format
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Write the keys to files
    with open("private_key.pem", "wb") as private_key_file:
        private_key_file.write(private_key_pem)

    with open("public_key.pem", "wb") as public_key_file:
        public_key_file.write(public_key_pem)

class JWTAuthBackend(AuthenticationBackend):
    '''
    Authenticate with JWT using the public key configured
    '''
    def __init__(self) -> None:
        super().__init__()
        self.jwt_pub_path = os.environ.get('JWT_PUB_PATH', os.getcwd() + '/jwt.pub')
        # raise error if JWT_PUB_PATH is not found
        if not self.jwt_pub_path:
            raise AuthenticationError('JWT Public key path not configured')
        if not os.path.exists(self.jwt_pub_path):
            raise AuthenticationError(f'JWT Public key not found in path {self.jwt_pub_path}')
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