import os
import time
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================================
# CONFIGURACIÓN GENERAL Y CANAL DE PAGOS
# ==========================================
TOKEN = "8810406805:AAGYzuFwJUdW6RAQk3hNoxXeRIt7QzUo2R8"
ADMIN_ID = 7756783743  
WALLET_BEP20 = "0xEa02dAD3De9F44dC87b701D48934472dACd4bEc5"

# CONFIGURACIÓN DEL CANAL DE PAGOS (PRUEBA SOCIAL)
CANAL_PAGOS_LINK = "https://t.me/TuCanalDePagos"  # Reemplaza con el enlace público de tu canal
CANAL_PAGOS_ID = "@TuCanalDePagos"                # Reemplaza con el alias o ID del canal donde el bot es Admin

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ESCRITORIO_USUARIO = os.path.join(os.path.expanduser("~"), "Desktop")
ARCHIVO_JSON = os.path.join(DIRECTORIO_ACTUAL, "usuarios_fwb.json")

rutas_posibles = [
    os.path.join(DIRECTORIO_ACTUAL, "header.png"),
    os.path.join(DIRECTORIO_ACTUAL, "header.png.png"),
    os.path.join(ESCRITORIO_USUARIO, "header.png"),
    os.path.join(ESCRITORIO_USUARIO, "header.png.png")
]

IMAGEN_HEADER = None
for ruta in rutas_posibles:
    if os.path.exists(ruta):
        IMAGEN_HEADER = ruta
        break

# TEMÁTICA ORIGINAL: NIVELES DE MATERIALES
PLANES = {
    "madera": {"nombre": "Nivel Madera 🪵", "precio": 5, "retorno": 7.5},
    "oro": {"nombre": "Nivel Oro 🥇", "precio": 10, "retorno": 15.0},
    "diamante": {"nombre": "Nivel Diamante 💎", "precio": 20, "retorno": 30.0}
}

# ==========================================
# BASE DE DATOS PERSISTENTE (JSON LOCAL)
# ==========================================
def cargar_usuarios():
    if os.path.exists(ARCHIVO_JSON):
        try:
            with open(ARCHIVO_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"Error al cargar usuarios_fwb.json: {e}")
            return {}
    return {}

def guardar_usuarios():
    try:
        with open(ARCHIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error al guardar usuarios_fwb.json: {e}")

usuarios = cargar_usuarios()
solicitudes_retiro = []

bot = telebot.TeleBot(TOKEN, threaded=True, num_threads=4)

def obtener_usuario(user_id, username):
    if user_id not in usuarios:
        usuarios[user_id] = {
            "user_id": user_id,
            "username": username,
            "patrocinador": None,
            "plan": None,
            "referidos_mismo_plan": [],
            "saldo_retirable": 0.0,
            "pago_pendiente": None
        }
        guardar_usuarios()
    return usuarios[user_id]

# ==========================================
# MENÚS PRINCIPALES
# ==========================================
def menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🛒 Adquirir Nivel", callback_data="ver_planes"),
        InlineKeyboardButton("👤 Mi Perfil", callback_data="mi_perfil"),
        InlineKeyboardButton("🔗 Link de Referido", callback_data="mi_link"),
        InlineKeyboardButton("💸 Retirar Saldo", callback_data="solicitar_retiro"),
        InlineKeyboardButton("📜 Canal de Pagos", url=CANAL_PAGOS_LINK),
        InlineKeyboardButton("ℹ️ ¿Cómo Funciona?", callback_data="como_funciona"),
        InlineKeyboardButton("💬 Soporte Técnico", url="https://t.me/friendwhitbenefitsS_bot")
    )
    return markup

def menu_planes():
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("🪵 Nivel Madera (5 USDT)", callback_data="comprar_madera"),
        InlineKeyboardButton("🥇 Nivel Oro (10 USDT)", callback_data="comprar_oro"),
        InlineKeyboardButton("💎 Nivel Diamante (20 USDT)", callback_data="comprar_diamante"),
        InlineKeyboardButton("⬅️ Volver al Menú", callback_data="menu_principal")
    )
    return markup

def enviar_menu_con_foto(chat_id):
    texto_bienvenida = (
        "🤝 *¡BIENVENIDO A FRIENDS WITH BENEFITS!* 🤝\n\n"
        "Construye tu red, impulsa causas sociales y recibe beneficios por ciclo completado."
    )
    
    if IMAGEN_HEADER and os.path.exists(IMAGEN_HEADER):
        try:
            with open(IMAGEN_HEADER, 'rb') as photo:
                bot.send_photo(
                    chat_id,
                    photo,
                    caption=texto_bienvenida,
                    parse_mode="Markdown",
                    reply_markup=menu_principal(),
                    timeout=120
                )
                return
        except Exception as e:
            print(f"Aviso al enviar foto: {e}. Enviando menú en texto...")
    
    bot.send_message(
        chat_id,
        texto_bienvenida,
        parse_mode="Markdown",
        reply_markup=menu_principal()
    )

# ==========================================
# MANEJADORES DE EVENTOS Y LÓGICA
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        args = message.text.split()

        user = obtener_usuario(user_id, username)

        if len(args) > 1 and user["patrocinador"] is None:
            try:
                patrocinador_id = int(args[1])
                if patrocinador_id != user_id and patrocinador_id in usuarios:
                    user["patrocinador"] = patrocinador_id
                    guardar_usuarios()
            except ValueError:
                pass

        enviar_menu_con_foto(message.chat.id)
    except Exception as e:
        print(f"Error en start: {e}")

@bot.callback_query_handler(func=lambda call: not call.data.startswith(("pagar_retiro_", "rechazar_retiro_", "ver_referidos_")))
def callback_listener(call):
    try:
        user_id = call.from_user.id
        username = call.from_user.username or call.from_user.first_name
        user = obtener_usuario(user_id, username)

        if call.data == "menu_principal":
            enviar_menu_con_foto(call.message.chat.id)

        elif call.data == "ver_planes":
            bot.send_message(call.message.chat.id, "Selecciona el Nivel que deseas adquirir:", reply_markup=menu_planes())

        elif call.data.startswith("comprar_"):
            plan_key = call.data.split("_")[1]
            plan_info = PLANES[plan_key]
            user["pago_pendiente"] = plan_key
            guardar_usuarios()

            texto_instrucciones = (
                f"📥 ADQUIRIR {plan_info['nombre'].upper()}\n\n"
                f"• Monto a enviar: {plan_info['precio']} USDT\n"
                f"• Red: BNB Smart Chain (BEP20)\n\n"
                "👇 Toca la dirección de abajo para copiarla directamente:"
            )
            bot.send_message(call.message.chat.id, texto_instrucciones)
            bot.send_message(call.message.chat.id, f"`{WALLET_BEP20}`", parse_mode="Markdown")
            bot.send_message(
                call.message.chat.id,
                "⚠️ Una vez realizada la transferencia, envía la captura o foto del comprobante en este chat."
            )

        elif call.data == "mi_perfil":
            plan_str = PLANES[user["plan"]]["nombre"] if user["plan"] else "Ninguno"
            texto = (
                f"👤 *TU PERFIL EN FRIENDS WITH BENEFITS*\n\n"
                f"• *Usuario:* @{user['username']}\n"
                f"• *ID:* {user_id}\n"
                f"• *Nivel Activo:* {plan_str}\n"
                f"• *Referidos en tu Nivel:* {len(user['referidos_mismo_plan'])} / 2\n"
                f"• *Saldo Retirable:* {user['saldo_retirable']} USDT"
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅️ Volver al Menú", callback_data="menu_principal"))
            bot.send_message(call.message.chat.id, texto, parse_mode="Markdown", reply_markup=markup)

        elif call.data == "mi_link":
            link = f"https://t.me/{bot.get_me().username}?start={user_id}"
            bot.send_message(
                call.message.chat.id,
                f"🔗 *Tu enlace único de invitado:*\n{link}\n\nInvita a 2 amigos con tu mismo nivel para completar tu ciclo.",
                parse_mode="Markdown"
            )

        elif call.data == "solicitar_retiro":
            if user["saldo_retirable"] <= 0:
                bot.send_message(call.message.chat.id, "⚠️ No tienes saldo disponible para retirar.")
            else:
                monto = user["saldo_retirable"]
                
                registro = {
                    "user_id": user_id,
                    "username": username,
                    "monto": monto,
                    "estado": "Pendiente"
                }
                solicitudes_retiro.append(registro)

                markup_admin = InlineKeyboardMarkup(row_width=2)
                markup_admin.add(
                    InlineKeyboardButton("🟢 Pagado", callback_data=f"pagar_retiro_{user_id}_{monto}"),
                    InlineKeyboardButton("🔴 Rechazar", callback_data=f"rechazar_retiro_{user_id}")
                )
                markup_admin.add(
                    InlineKeyboardButton("🔍 Ver Estado Referidos", callback_data=f"ver_referidos_{user_id}")
                )

                ref_activos = len(user["referidos_mismo_plan"])
                bot.send_message(
                    ADMIN_ID,
                    f"💸 *SOLICITUD DE RETIRO DE SALDO*\n\n"
                    f"• *Usuario:* @{username} (ID: {user_id})\n"
                    f"• *Monto a pagar:* {monto} USDT\n"
                    f"• *Referidos Pagados:* {ref_activos} / 2",
                    parse_mode="Markdown",
                    reply_markup=markup_admin
                )
                
                bot.send_message(call.message.chat.id, "📩 Tu solicitud de retiro ha sido enviada al administrador.")

        elif call.data == "como_funciona":
            texto_explicativo = (
                "🤝 *¿CÓMO FUNCIONA FRIENDS WITH BENEFITS?*\n\n"
                "1️⃣ *SELECCIONA TU NIVEL*\n"
                "• *Madera ($5 USDT):* Recibes 7.50 USDT al ciclar.\n"
                "• *Oro ($10 USDT):* Recibes 15.00 USDT al ciclar.\n"
                "• *Diamante ($20 USDT):* Recibes 30.00 USDT al ciclar.\n\n"
                "2️⃣ *SISTEMA DE MATRIZ (2x1)*\n"
                "Comparte tu enlace personal. Cuando 2 referidos entren en tu mismo nivel, completas tu ciclo con un **50% de ganancia neta**.\n\n"
                "3️⃣ *FONDO SOCIAL (25%)*\n"
                "El 25% sobrante de cada ciclo financia directamente obras sociales universitarias e iniciativas comunitarias.\n\n"
                "4️⃣ *SOLICITA TU RETIRO*\n"
                "El saldo acumulado se envía a tu billetera BEP20 una vez verificada tu solicitud."
            )
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("⬅️ Volver al Menú", callback_data="menu_principal"))
            bot.send_message(call.message.chat.id, texto_explicativo, parse_mode="Markdown", reply_markup=markup)

        elif call.data.startswith("aprobar_"):
            _, cliente_id, plan_key = call.data.split("_")
            cliente_id = int(cliente_id)
            cliente = usuarios[cliente_id]

            cliente["plan"] = plan_key
            cliente["pago_pendiente"] = None

            planilla = (
                f"📄 COMPROBANTE DE ACTIVACIÓN\n"
                f"=========================\n"
                f"👤 Usuario: @{cliente['username']}\n"
                f"🆔 ID: {cliente_id}\n"
                f"🧱 Nivel Adquirido: {PLANES[plan_key]['nombre']}\n"
                f"💵 Monto Aprobado: {PLANES[plan_key]['precio']} USDT\n"
                f"🎯 Retorno Estimado: {PLANES[plan_key]['retorno']} USDT\n"
                f"✅ Estado: ACTIVADO\n"
                f"=========================\n\n"
                f"🎉 ¡Tu cuenta está lista para empezar!"
            )

            destinatarios = [cliente_id, ADMIN_ID]
            if CANAL_PAGOS_ID:
                destinatarios.append(CANAL_PAGOS_ID)

            for dest in destinatarios:
                try:
                    if IMAGEN_HEADER and os.path.exists(IMAGEN_HEADER):
                        with open(IMAGEN_HEADER, 'rb') as photo:
                            bot.send_photo(dest, photo, caption=planilla)
                    else:
                        bot.send_message(dest, planilla)
                except Exception as ex:
                    print(f"Aviso al enviar planilla a {dest}: {ex}")

            bot.answer_callback_query(call.id, "Nivel aprobado y publicado.")

            patrocinador_id = cliente["patrocinador"]
            if patrocinador_id and patrocinador_id in usuarios:
                patrocinador = usuarios[patrocinador_id]
                if patrocinador["plan"] == plan_key and cliente_id not in patrocinador["referidos_mismo_plan"]:
                    patrocinador["referidos_mismo_plan"].append(cliente_id)

                    if len(patrocinador["referidos_mismo_plan"]) == 2:
                        ganancia = PLANES[plan_key]["retorno"]
                        patrocinador["saldo_retirable"] += ganancia

                        mensaje_exito = (
                            f"🎉 *¡CICLO COMPLETADO CON ÉXITO!*\n\n"
                            f"Hola @{patrocinador['username']}, tus 2 referidos han activado su nivel.\n"
                            f"• *Ganancia Acumulada:* {ganancia} USDT\n\n"
                            "Ya puedes solicitar tu retiro desde el menú principal."
                        )
                        bot.send_message(patrocinador_id, mensaje_exito, parse_mode="Markdown")

            guardar_usuarios()

        elif call.data.startswith("rechazar_"):
            cliente_id = int(call.data.split("_")[1])
            bot.send_message(cliente_id, "❌ Tu pago fue rechazado. Contacta con soporte para ayuda.")
            bot.answer_callback_query(call.id, "Rechazado.")

    except Exception as e:
        print(f"Error en callback: {e}")

# ==========================================
# SECCIÓN ADMINISTRATIVA
# ==========================================
@bot.callback_query_handler(func=lambda call: call.data.startswith(("pagar_retiro_", "rechazar_retiro_", "ver_referidos_")))
def procesar_retiro_admin(call):
    if call.from_user.id != ADMIN_ID:
        return

    partes = call.data.split("_")
    accion = partes[0]
    
    if accion == "ver" and partes[1] == "referidos":
        cliente_id = int(partes[2])
        if cliente_id in usuarios:
            u = usuarios[cliente_id]
            ref_completados = len(u["referidos_mismo_plan"])
            faltantes = max(0, 2 - ref_completados)
            lista_ids = ", ".join([f"{rid}" for rid in u["referidos_mismo_plan"]]) if ref_completados > 0 else "Ninguno"
            
            detalle = (
                f"🔎 *DETALLE DE REFERIDOS DE @{u['username']}*\n\n"
                f"• *Nivel:* {u['plan'].upper() if u['plan'] else 'Ninguno'}\n"
                f"• *Referidos Activos:* {ref_completados} / 2\n"
                f"• *Referidos Faltantes:* {faltantes}\n"
                f"• *IDs de Referidos:* {lista_ids}"
            )
            bot.send_message(ADMIN_ID, detalle, parse_mode="Markdown")
            bot.answer_callback_query(call.id)
        return

    if accion == "pagar":
        cliente_id = int(partes[2])
        monto = float(partes[3])
        
        if cliente_id in usuarios:
            usuarios[cliente_id]["saldo_retirable"] = 0.0
            guardar_usuarios()
            
        for r in solicitudes_retiro:
            if r["user_id"] == cliente_id and r["estado"] == "Pendiente":
                r["estado"] = "Completado"

        msg_retiro = (
            f"💸 RETIRO COMPLETADO\n"
            f"=========================\n"
            f"👤 Usuario: @{usuarios[cliente_id]['username']}\n"
            f"💵 Monto Pagado: {monto} USDT\n"
            f"✅ Estado: ENVIADO\n"
            f"=========================\n\n"
            f"🎉 ¡Gracias por formar parte de Friends with Benefits!"
        )

        bot.send_message(cliente_id, msg_retiro)
        bot.edit_message_text(f"✅ Retiro de {monto} USDT para @{usuarios[cliente_id]['username']} marcado como PAGADO.", ADMIN_ID, call.message.message_id)

        if CANAL_PAGOS_ID:
            try:
                bot.send_message(CANAL_PAGOS_ID, msg_retiro)
            except Exception as e:
                print(f"Error publicando retiro en canal: {e}")

    elif accion == "rechazar":
        cliente_id = int(partes[2])
        bot.send_message(cliente_id, "❌ Tu solicitud de retiro ha sido rechazada.")
        bot.edit_message_text(f"🔴 Retiro de {cliente_id} RECHAZADO.", ADMIN_ID, call.message.message_id)

@bot.message_handler(commands=['inactivos', 'inactivo'])
def listar_usuarios_inactivos(message):
    if message.from_user.id != ADMIN_ID: return
    inactivos = [u for u in usuarios.values() if u["plan"] is None and len(u["referidos_mismo_plan"]) == 0]
    if not inactivos:
        bot.reply_to(message, "📊 No hay usuarios inactivos.")
        return
    reporte = f"👥 USUARIOS SIN NIVEL Y SIN REFERIDOS (Total: {len(inactivos)})\n\n"
    for user in inactivos:
        reporte += f"• @{user['username']} (ID: {user['user_id']})\n"
    bot.send_message(ADMIN_ID, reporte)

@bot.message_handler(commands=['totalusuarios', 'total_usuarios'])
def listar_total_usuarios(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(ADMIN_ID, f"📊 Total de Usuarios: {len(usuarios)}")

@bot.message_handler(content_types=['photo'])
def recibir_comprobante(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name
        user = obtener_usuario(user_id, username)

        plan_key = user["pago_pendiente"]
        if not plan_key:
            bot.reply_to(message, "⚠️ No tienes una orden de compra pendiente.")
            return

        plan_info = PLANES[plan_key]

        markup_admin = InlineKeyboardMarkup()
        markup_admin.add(
            InlineKeyboardButton("🟢 Aprobar Nivel", callback_data=f"aprobar_{user_id}_{plan_key}"),
            InlineKeyboardButton("🔴 Rechazar", callback_data=f"rechazar_{user_id}")
        )

        caption = (
            f"🚨 NUEVO COMPROBANTE DE PAGO\n\n"
            f"• Usuario: @{username} (ID: {user_id})\n"
            f"• Nivel: {plan_info['nombre']}\n"
            f"• Monto: {plan_info['precio']} USDT"
        )

        file_id = message.photo[-1].file_id
        bot.send_photo(ADMIN_ID, file_id, caption=caption, reply_markup=markup_admin)
        bot.reply_to(message, "📩 Tu comprobante ha sido enviado a revisión.")
    except Exception as e:
        print(f"Error al recibir comprobante: {e}")

# ==========================================
# BUCLE DE EJECUCIÓN CONTINUA
# ==========================================
print("Bot Friend of Benefits iniciado con éxito...")

while True:
    try:
        bot.polling(non_stop=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"⚠️ Parpadeo de conexión: {e}. Reintentando en 5 segundos...")
        time.sleep(5)