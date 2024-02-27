"""
Dependências do Projeto:

- pip install fastapi  -> Responsável pela Criação da API
- pip install uvicorn -> Responsável pela Atualização da API sempre que o Código for Atualizado.

- pip install motor   -> Responsável pela Comunicação com o Banco de Dados MongoDB de Forma Assíncrona.

- pip install python-dotenv -> Responsável por permitir a utilização de Variáveis de Ambiente (.env).

Executando a aplicação:

- uvicorn main:app --reload

Observação:

- O FastAPI usa o Pydantic para definir modelos de dados (BaseModel) que são usados para validar os dados recebidos em
requisições e serializar os dados de resposta em JSON.

- O Pydantic é integrado ao FastAPI e fornece uma maneira conveniente e poderosa de definir e validar os dados
em sua aplicação.

- AsyncIOMotorClient é uma classe fornecida pelo motor que representa o cliente para interagir com um banco de dados
MongoDB de forma assíncrona. Ele é usado para estabelecer uma conexão com o banco de dados e executar
operações assíncronas.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
# import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from dotenv import load_dotenv
import os

# Carrega as variáveis de ambiente do arquivo .env:
load_dotenv()

# Pegando as variáveis de ambiente carregadas:
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

MONGODB_URL = f"mongodb+srv://{"witoroliveira"}:{"70jw9Zsb3MjVaNuH"}@firstdb.h7xha7y.mongodb.net/?retryWrites=true&w=majority&appName=FirstDB"
client = AsyncIOMotorClient(MONGODB_URL)  # ->  Cria um cliente Assíncrono para se Conectar ao banco de dados MongoDB.
db = client["test"]  # -> Nome do Banco de Dados do Projeto.


# Função para Fechar a Conexão com o Banco de Dados
async def close_mongo_connection():
    client.close()


# Criando a Aplicação FastAPI
app = FastAPI()

# Simulação do Banco de Dados:
pessoas_exemplo = [{"id": 1, "nome": "Joao", "idade": 35, "role": "Admin"},
                   {"id": 2, "nome": "Maria", "idade": 28, "role": "User"},
                   {"id": 3, "nome": "Renato", "idade": 26, "role": "Admin"}]


# Modelo **Pydantic** para validar os dados de uma nova Pessoa:
class User(BaseModel):
    cpf: str
    name: str
    first_name: str
    last_name: str
    email: str
    age: int


class Admin(BaseModel):
    cpf: str
    name: str
    first_name: str
    last_name: str
    email: str
    age: int


class UpdateUser(BaseModel):
    name: str = None
    first_name: str = None
    last_name: str = None
    email: str = None
    age: int = None


class UpdateAdmin(BaseModel):
    name: str = None
    first_name: str = None
    last_name: str = None
    email: str = None
    age: int = None


# Criação das Rotas:

# Rotas de Pessoas:
# ROTAS GET:
@app.get("/user")
async def get_all_users():
    # pessoas = await db.people.find().to_list(length=None)
    # return pessoas

    # Acessar a coleção "people":
    users = await db.users.find().to_list(length=None)

    """
    Converte o ObjectId para string.
    Isso é necessário pois o ObjectId é um tipo específico de dado usado pelo MongoDB para identificar documentos 
    de forma única. No entanto, o ObjectId não é diretamente serializável para JSON.
    Para corrigir esse erro, devemos converter explicitamente o ObjectId para uma string antes de retornar os dados.
    """
    for user in users:
        user["_id"] = str(user["_id"])  # -> Convertendo o _id para uma String.

    return users


# Pegando Pessoa Especifica
@app.get("/user/{cpf}")
async def get_user_by_cpf(cpf: str):
    user = await db.users.find_one({"cpf": cpf})

    if user:
        user["_id"] = str(user["_id"])
        return user
    else:
        return {"message": "Usuário não encontrado!"}


# ROTA POST:
@app.post("/user/create")
async def create_user(user: User):
    # if pessoa.nome == "":
    #     raise HTTPException(status_code=404, detail="O nome não pode estar em branco!")

    # nova_pessoa = {"id": len(pessoas) + 1, "nome": pessoa.nome, "idade": pessoa.idade, "role": pessoa.role}
    # pessoas.append(nova_pessoa)

    existe_cpf = await procura_cpf(user.cpf, "user")
    existe_email = await procura_email(user.email, "user")

    if (not existe_cpf) and (not existe_email):
        new_user = {"cpf": user.cpf, "name": user.name, "first_name": user.first_name,
                    "last_name": user.last_name, "email": user.email, "age": user.age,
                    "status": "active", "role": "user"}
        await db.users.insert_one(new_user)

        return {"message": "Pessoa criada com sucesso!"}
    elif (existe_cpf is None) or (existe_email is None):
        return {"message": "Erro interno."}
    else:
        if existe_cpf:
            return {"message": "CPF já cadastrado!"}
        elif existe_email:
            return {"message": "E-mail já cadastrado!"}


# ROTA PATCH:
@app.patch("/user/{cpf}")
async def update_user_by_cpf(cpf: str, update_infos: UpdateUser):
    update_infos = update_infos.dict(exclude_unset=True)

    existe_email = False

    if "email" in update_infos.keys():
        existe_email = await procura_email(update_infos["email"], "user")

    if not existe_email:
        request = await db.users.update_one({"cpf": cpf}, {"$set": update_infos})

        # Verifica se exatamente um documento foi modificado durante a operação de atualização: (Usamos o update_one)
        if request.modified_count == 1:
            if len(update_infos) == 1:
                return {f"message": f"O campo {list(update_infos.keys())[0]} foi alterado com sucesso!"}
            else:
                return {f"message": f"Os campos | {' | '.join(list(update_infos.keys()))} | foram alterados com sucesso!"}
        else:
            return {"message": "Falha ao atualizar pessoa!"}
    else:
        return {"message": "E-mail já cadastrado!"}


# ROTA DELETE:
@app.delete("/user/delete/{cpf}")
async def delete_user_by_cpf(cpf: str):
    request = await db.users.delete_one({"cpf": cpf})

    if request.deleted_count == 1:
        return {"message": "Usuário removido com sucesso!"}
    else:
        return {"message": "Erro ao remover usuário!"}


# Rotas de Admin:
# ROTAS GET:
@app.get("/admin")
async def get_all_admin():
    admins = await db.admins.find().to_list(length=None)

    for admin in admins:
        admin["_id"] = str(admin["_id"])

    return admins


# Pegando Admin Especifico
@app.get("/admin/{cpf}")
async def get_admin_by_cpf(cpf: str):
    admin = await db.admins.find_one({"cpf": cpf})

    if admin:
        admin["_id"] = str(admin["_id"])
        return admin
    else:
        return {"message": "Admin não encontrado!"}


# ROTA POST:
@app.post("/admin/create")
async def create_admin(admin: Admin):
    existe_cpf = await procura_cpf(admin.cpf, "admin")
    existe_email = await procura_email(admin.email, "admin")

    if (not existe_cpf) and (not existe_email):
        novo_admin = {"cpf": admin.cpf, "name": admin.name, "first_name": admin.first_name,
                      "last_name": admin.last_name,
                      "email": admin.email, "age": admin.age, "status": "active", "role": "admin"}

        await db.admins.insert_one(novo_admin)

        return {"message": "Admin criado com sucesso!"}
    elif (existe_cpf is None) or (existe_email is None):
        return {"message": "Erro interno."}
    else:
        if existe_cpf:
            return {"message": "CPF já cadastrado!"}
        elif existe_email:
            return {"message": "E-mail já cadastrado!"}


# ROTA PATCH:
@app.patch("/admin/{cpf}")
async def update_admin_by_cpf(cpf: str, update_infos: UpdateAdmin):
    update_infos = update_infos.dict(exclude_unset=True)

    existe_email = False

    if "email" in update_infos.keys():
        existe_email = await procura_email(update_infos["email"], "admin")

    if not existe_email:
        request = await db.admins.update_one({"cpf": cpf}, {"$set": update_infos})

        if request.modified_count == 1:
            if len(update_infos) == 1:
                return {"message": f"O campo {list(update_infos.keys())[0]} foi alterado com sucesso!"}
            else:
                return {"message": f"Os campos | {' | '.join(list(update_infos.keys()))} | foram alterados com suscesso!"}
        else:
            return {"message": "Falha ao atualizar admin!"}
    else:
        return {"message": "E-mail já cadastrado!"}


# ROTA DELETE:
@app.delete("/admin/delete/{cpf}")
async def delete_admin_by_cpf(cpf: str):
    request = await db.admins.delete_one({"cpf": cpf})

    if request.deleted_count == 1:
        return {"message": "Admin removido com sucesso!"}
    else:
        return {"message": "Erro ao remover admin!"}


# VALIDAÇÕES:
async def procura_cpf(cpf: str, collection: str) -> bool | None:
    if collection == "user":
        request = await db.users.find({"cpf": cpf}).to_list(length=None)
    elif collection == "admin":
        request = await db.admins.find({"cpf": cpf}).to_list(length=None)
    else:
        return None

    if request.__len__() > 0:
        return True  # -> Retorna True se existe.
    else:
        return False  # -> Retorna False se não existe.


async def procura_email(email: str, collection: str) -> bool | None:
    if collection == "user":
        request = await db.users.find({"email": email}).to_list(length=None)
    elif collection == "admin":
        request = await db.admins.find({"email": email}).to_list(length=None)
    else:
        return None

    if request.__len__() > 0:
        return True
    else:
        return False
