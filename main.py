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
class Pessoa(BaseModel):
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


class UpdatePessoa(BaseModel):
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
@app.get("/pessoas")
async def get_pessoas():
    # pessoas = await db.people.find().to_list(length=None)
    # return pessoas

    # Acessar a coleção "people":
    pessoas = await db.people.find().to_list(length=None)

    """
    Converte o ObjectId para string.
    Isso é necessário pois o ObjectId é um tipo específico de dado usado pelo MongoDB para identificar documentos 
    de forma única. No entanto, o ObjectId não é diretamente serializável para JSON.
    Para corrigir esse erro, devemos converter explicitamente o ObjectId para uma string antes de retornar os dados.
    """
    for person in pessoas:
        person["_id"] = str(person["_id"])  # -> Convertendo o _id para uma String.

    return pessoas


# Pegando Pessoa Especifica
@app.get("/pessoas/{cpf}")
async def get_pessoa_by_cpf(cpf: str):
    pessoa = await db.people.find_one({"cpf": cpf})

    if pessoa:
        pessoa["_id"] = str(pessoa["_id"])
        return pessoa
    else:
        return {"message": "Pessoa não encontrada!"}


# ROTA POST:
@app.post("/pessoas/create")
async def create_pessoa(pessoa: Pessoa):
    # if pessoa.nome == "":
    #     raise HTTPException(status_code=404, detail="O nome não pode estar em branco!")

    # nova_pessoa = {"id": len(pessoas) + 1, "nome": pessoa.nome, "idade": pessoa.idade, "role": pessoa.role}
    # pessoas.append(nova_pessoa)

    nova_pessoa = {"cpf": pessoa.cpf, "name": pessoa.name, "first_name": pessoa.first_name,
                   "last_name": pessoa.last_name, "email": pessoa.email, "age": pessoa.age,
                   "status": "active", "role": "user"}
    await db.people.insert_one(nova_pessoa)

    return {"message": "Pessoa criada com sucesso!"}


# ROTA PATCH:
@app.patch("/pessoas/{cpf}")
async def update_pessoa(cpf: str, update_infos: UpdatePessoa):
    update_infos = update_infos.dict(exclude_unset=True)

    request = await db.people.update_one({"cpf": cpf}, {"$set": update_infos})

    # Verifica se exatamente um documento foi modificado durante a operação de atualização: (Usamos o update_one)
    if request.modified_count == 1:
        if len(update_infos) == 1:
            return {f"message": f"O campo {list(update_infos.keys())[0]} foi alterado com sucesso!"}
        else:
            return {f"message": f"Os campos | {' | '.join(list(update_infos.keys()))} | foram alterados com sucesso!"}
    else:
        return {"message": "Falha ao atualizar pessoa!"}


# ROTA DELETE:
@app.delete("/pessoas/delete/{cpf}")
async def delete_pessoa(cpf: str):
    request = await db.people.delete_one({"cpf": cpf})

    if request.deleted_count == 1:
        return {"message": "Usuário removido com sucesso!"}
    else:
        return {"message": "Erro ao remover pessoa!"}


# Rotas de Admin:
# ROTAS GET:
@app.get("/admin")
async def get_admin():
    admins = await db.admins.find().to_list(length=None)

    for admin in admins:
        admin["_id"] = str(admin["_id"])

    return admins


# Pegando Admin Especifico
@app.get("/admin/{cpf}")
async def get_pessoa_by_cpf(cpf: str):
    admin = await db.admins.find_one({"cpf": cpf})

    if admin:
        admin["_id"] = str(admin["_id"])
        return admin
    else:
        return {"message": "Admin não encontrado!"}


# ROTA POST:
@app.post("/admin/create")
async def create_admin(admin: Admin):
    novo_admin = {"cpf": admin.cpf, "name": admin.name, "first_name": admin.first_name, "last_name": admin.last_name,
                  "email": admin.email, "age": admin.age, "status": "active", "role": "admin"}

    await db.admins.insert_one(novo_admin)

    return {"message": "Admin criado com sucesso!"}


# ROTA PATCH:
@app.patch("/admin/{cpf}")
async def update_admin(cpf: str, update_infos: UpdateAdmin):
    update_infos = update_infos.dict(exclude_unset=True)

    request = await db.admins.update_one({"cpf": cpf}, {"$set": update_infos})

    if request.modified_count == 1:
        if len(update_infos) == 1:
            return {"message": f"O campo {list(update_infos.keys())[0]} foi alterado com sucesso!"}
        else:
            return {"message": f"Os campos | {' | '.join(list(update_infos.keys()))} | foram alterados com suscesso!"}
    else:
        return {"message":  "Falha ao atualizar admin!"}


# ROTA DELETE:
@app.delete("/admin/delete/{cpf}")
async def delete_admin(cpf: str):
    request = await db.admins.delete_one({"cpf": cpf})

    if request.deleted_count == 1:
        return {"message": "Admin removido com sucesso!"}
    else:
        return {"message": "Erro ao remover admin!"}
