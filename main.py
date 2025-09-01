from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

class MessageRequest(BaseModel):
    from_: str
    body: str

user_steps = {}
user_data = {}
user_blocked_until = {}
user_silence_until = {}

menu_text = (
    "Escolha uma das opções do menu principal digitando o número correspondente:\n\n"
    "1️⃣ **Agendar um Reparo** 🔧\n"
    "2️⃣ **Orçamento de Serviço** 💰\n"
    "3️⃣ **Falar com um Atendente** 🗣️\n"
    "4️⃣ **Endereço e Horário de Funcionamento** 📍"
)

endereco_horario_text = (
    "Nosso endereço é: 📍 Rua Arealva 72\n\n"
    "Horário de funcionamento 🕒:\n"
    "Segunda a Sábado: 09:00 às 18:00\n"
    "Domingo/Feriados: 09:00 às 13:00"
)

def set_block(user_id: str):
    user_blocked_until[user_id] = datetime.now() + timedelta(minutes=1)

def set_silence(user_id: str, minutes: int = 10):
    user_silence_until[user_id] = datetime.now() + timedelta(minutes=minutes)

@app.post("/message")
async def handle_message(message: MessageRequest):
    user_id = message.from_
    body = message.body.strip()

    # === BLOQUEIO DE MENSAGENS EM GRUPOS ===
    if "@g.us" in user_id:
        return {"reply": "", "action": "group_blocked"}

    # === BLOQUEIO DE SILÊNCIO ===
    if user_id in user_silence_until:
        if datetime.now() < user_silence_until[user_id]:
            return {"reply": "", "action": "silence_active"}
        else:
            del user_silence_until[user_id]

    # === BLOQUEIO TEMPORÁRIO ===
    if user_id in user_blocked_until:
        if datetime.now() < user_blocked_until[user_id]:
            return {"reply": "", "action": "blocked"}
        else:
            del user_blocked_until[user_id]

    # === LÓGICA DE ATENDIMENTO ===

    if user_id not in user_steps:
        user_steps[user_id] = "menu"
        return {
            "reply": f"Olá! 👋 Bem-vindo(a) à MxTech! Me chamo Lucas, sou assistente virtual 🤖 e estou aqui para ajudar com seu celular.\n\n{menu_text}",
            "action": "menu"
        }

    step = user_steps[user_id]

    if step == "menu":
        if body == "1":
            user_steps[user_id] = "agendar_marca"
            return {"reply": "Você escolheu **Agendar um Reparo** 🔧\nQual a marca e modelo do aparelho? (Ex: iPhone 14, Samsung S23)", "action": "agendar_marca"}
        elif body == "2":
            user_steps[user_id] = "orcamento_servico"
            return {"reply": "Você escolheu **Orçamento de Serviço** 💰\nEscolha o serviço:\n1️⃣ Troca de Tela\n2️⃣ Troca de Bateria\n3️⃣ Reparo de Placa\n4️⃣ Problemas de Software\n5️⃣ Outro", "action": "orcamento_servico"}
        elif body == "3":
            user_steps[user_id] = "done"
            set_block(user_id)
            return {"reply": "Certo! 😎 Encaminhando você para um de nossos atendentes... Por favor, aguarde ⏳", "action": "end"}
        elif body == "4":
            user_steps[user_id] = "done"
            set_block(user_id)
            return {"reply": endereco_horario_text, "action": "end"}
        else:
            return {"reply": "Digite um número válido (1 a 4).", "action": "menu"}

    if step == "agendar_marca":
        if not body:
            return {"reply": "Informe a marca e modelo do aparelho.", "action": "agendar_marca"}
        user_data[user_id] = {"marca_modelo": body}
        user_steps[user_id] = "agendar_problema"
        return {"reply": "Descreva brevemente o problema do aparelho (Ex: Tela quebrada, não liga, sem áudio).", "action": "agendar_problema"}

    if step == "agendar_problema":
        if not body:
            return {"reply": "Descreva o problema do aparelho para prosseguirmos.", "action": "agendar_problema"}
        user_data[user_id]["problema"] = body
        user_steps[user_id] = "agendar_contato"
        return {"reply": "Informe seu Nome para finalizar o seu cadastro 🗣️", "action": "agendar_contato"}

    if step == "agendar_contato":
        parts = body.split()
        if len(parts) >= 2:
            telefone = parts[-1]
            nome = " ".join(parts[:-1])
        else:
            nome, telefone = body, ""
        user_data[user_id]["nome"] = nome
        user_data[user_id]["telefone"] = telefone
        user_data[user_id]["data_agendamento"] = datetime.now().isoformat()
        user_steps[user_id] = "done"
        set_block(user_id)
        return {
            "reply": f"✅ Confirmação concluída!\n\nPerfeito, {nome}! Seu agendamento para *{user_data[user_id]['marca_modelo']}* com o problema '*{user_data[user_id]['problema']}*' foi registrado.\nEntraremos em contato em breve. Obrigado!",
            "action": "end"
        }

    if step == "orcamento_servico":
        servicos = {"1": "Troca de Tela", "2": "Troca de Bateria", "3": "Reparo de Placa", "4": "Problemas de Software", "5": "Outro"}
        if body not in servicos:
            return {"reply": "Escolha um número válido de serviço (1 a 5).", "action": "orcamento_servico"}
        user_data[user_id] = {"servico": servicos[body]}
        user_steps[user_id] = "orcamento_marca"
        return {"reply": "Qual a marca e modelo do aparelho? (Ex: iPhone 14, Samsung S23)", "action": "orcamento_marca"}

    if step == "orcamento_marca":
        if not body:
            return {"reply": "Informe a marca e modelo do aparelho 🗣️", "action": "orcamento_marca"}
        user_data[user_id]["marca_modelo"] = body
        user_steps[user_id] = "orcamento_contato"
        return {"reply": "Informe seu Nome para finalizar o seu cadastro.", "action": "orcamento_contato"}

    if step == "orcamento_contato":
        parts = body.split()
        if len(parts) >= 2:
            telefone = parts[-1]
            nome = " ".join(parts[:-1])
        else:
            nome, telefone = body, ""
        user_data[user_id]["nome"] = nome
        user_data[user_id]["telefone"] = telefone
        user_data[user_id]["data_pedido"] = datetime.now().isoformat()
        user_steps[user_id] = "done"
        set_block(user_id)
        return {
            "reply": f"✅ Pedido registrado!\n\nObrigado, {nome}! Seu pedido de orçamento para *{user_data[user_id]['servico']}* no *{user_data[user_id]['marca_modelo']}* foi registrado.\nEntraremos em contato em breve.",
            "action": "end"
        }

    return {"reply": "Não entendi sua resposta. Digite novamente.", "action": step}
