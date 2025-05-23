import os

OPEN_AI_KEY=os.environ.get('OPEN_AI_KEY')
CHAT_VERSION=os.environ.get('CHAT_VERSION')
USER=os.environ.get('DB_USER')
DB_PASSWORD=os.environ.get('DB_PASSWORD')
SECRET_KEY=os.environ.get('SECRET_KEY')
HOST_NAME=os.environ.get('HOST_NAME')
DATABASE_NAME=os.environ.get('DB_NAME')
DATABASE_PORT=os.environ.get('DB_PORT')


ACCESS_EXPIRE_MINUTES = 20
ENCRYPTATION_ALGORITHM = "HS256"

