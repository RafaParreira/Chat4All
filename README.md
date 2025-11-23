# 🚀 **Chat4All – API & Interface de Chat**

Um sistema completo para gerenciamento de **usuários**, **salas**, **mensagens** e **arquivos**, com interface web integrada.
Toda a API está documentada automaticamente via **Swagger**, disponível apenas em execução e acessível em:

🔗 **[http://localhost:8000/docs#/](http://localhost:8000/docs#/)**

---

# 🔌 **Endpoints da API**

A seguir, os principais endpoints organizados por categoria com exemplos de requisições.

---

## 👤 **Usuários**

### ➕ Criar Usuário

`POST /users`

```json
{
  "username": "string"
}
```

---

### 🔍 Obter Usuário por ID

`GET /users/{user_id}`

```json
{
  "id": 0,
  "username": "string"
}
```

---

## 🏠 **Salas**

### ➕ Criar Sala

`POST /rooms`

```json
{
  "name": "string"
}
```

---

### 🔍 Obter Sala por ID

`GET /rooms/{room_id}`

```json
{
  "id": 0,
  "name": "string"
}
```

---

## 💬 **Mensagens**

### 📤 Enviar Mensagem (publicada no Kafka)

`POST /messages`

```json
{
  "room_id": 0,
  "sender_id": 0,
  "content": "string"
}
```

---

### 📥 Listar Mensagens de uma Sala

`GET /rooms/{room_id}/messages`

Retorna todas as mensagens armazenadas para a sala indicada.

---

## 📁 **Arquivos**

### ⬆️ Upload de Arquivo

`POST /v1/files/simple-upload`

Campos obrigatórios:

| Campo         | Tipo    | Descrição               |
| ------------- | ------- | ----------------------- |
| `uploader_id` | integer | ID do usuário que envia |
| `room_id`     | integer | Sala destino            |
| `upload`      | binary  | Arquivo                 |

---

### ⬇️ Download de Arquivo

`GET /v1/files/{file_id}/download`

| Parâmetro | Tipo   | Descrição     |
| --------- | ------ | ------------- |
| `file_id` | string | ID do arquivo |

---

# 📱 **Connector Mock – WhatsApp e Instagram**

Estes endpoints simulam a chegada de mensagens externas via **WhatsApp** e **Instagram**, permitindo testes de integração sem depender das APIs oficiais.

---

## 💬 WhatsApp – Mock Inbound

### 📥 Receber Mensagem

`POST /mock/whatsapp/inbound`

Exemplo de payload:

```json
{
  "sender": "5511999999999",
  "message": "Olá, isso é um teste via WhatsApp!",
  "room_id": 1
}
```

---

## 📸 Instagram – Mock Inbound

### 📥 Receber Mensagem

`POST /mock/instagram/inbound`

Exemplo de payload:

```json
{
  "sender": "usuario_ig",
  "message": "Mensagem enviada pelo Instagram!",
  "room_id": 1
}
```

---

# 🖥️ **Interface Web**

Uma interface gráfica está disponível para interação com o sistema:

🔗 **[http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)**

### Funções disponíveis:

* Visualizar **usuário atual**
* Alterar **sala**
* Ler todas as **mensagens**
* Enviar textos
* **Anexar arquivos**
* Enviar arquivo anexado
* Baixar arquivos recebidos (**"Baixar arquivo"**)

---

# ▶️ **Instruções de Execução**

1. Inicie o servidor backend (FastAPI):

   ```
   docker compose up --build
   ```
2. Acesse a interface web:
   👉 **[http://localhost:8000/static/index.html](http://localhost:8000/static/index.html)**
3. Utilize a interface para:

   * Entrar em salas
   * Criar mensagens
   * Enviar arquivos
   * Baixar arquivos

---

## 📝 Observações

* A interface apresenta um uso **intuitivo**, permitindo que o usuário navegue e interaja com facilidade.
* A aplicação possui **persistência de dados**: enquanto o servidor estiver em execução, mesmo que a aba do chat seja fechada, ao retorná-la é possível visualizar todas as mensagens que haviam sido enviadas e recebidas anteriormente.

---


