import os
OPEN_AI_KEY=os.environ.get('OPEN_AI_KEY')
CHAT_VERSION=os.environ.get('CHAT_VERSION')
USER=os.environ.get('DB_USER')
DB_PASSWORD=os.environ.get('DB_PASSWORD')
SECRET_KEY=os.environ.get('SECRET_KEY')
HOST_NAME=os.environ.get('HOST_NAME')
DATABASE_NAME=os.environ.get('DB_NAME')
DATABASE_PORT=os.environ.get('DB_PORT')

CHAT_MESSAGE_REQUEST= "Am nevoie sa-mi extragi valoarea corespunzatoare dintr - un text  si sa mi-o dai ca raspuns, fara alte cuvinte in plus pentru a putea folosi respectiva valoare in codul meu. De obicei, valorile căutate se află între ultimele două \\n. Cauta valoarea pentru: "
CHAT_MESSAGE_VERIFY_RESPONSE_FIRST = "Verifica daca raspunsul dat de tine pentru valoarea cautata se afla in textul pe care ti l-am dat, iar daca raspunsul se afla in text da-mi-l din nou fara explicatii, daca nu se afla in textul respectiv, da-mi rapsunsul corect: "
CHAT_MESSAGE_VERIFY_RESPONSE_SECOND = ""
ACCESS_EXPIRE_MINUTES = 120
ENCRYPTATION_ALGORITHM = "HS256"


