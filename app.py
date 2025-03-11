import logging
import os
from datetime import datetime
import pandas as pd
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Configuración de logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Estados del bot
HORA_ENTRADA, HORA_SALIDA = range(2)

# Ruta al archivo CSV donde se guardarán los datos
CSV_FILE = "data/registro_horas.csv"

# Función para cargar el CSV
def cargar_csv():
    try:
        # Asegurar que el directorio data existe
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        return pd.read_csv(CSV_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Fecha", "Entrada", "Salida", "Total Hrs"])

# Función para guardar el CSV
def guardar_csv(df):
    df.to_csv(CSV_FILE, index=False)

# Comando de inicio
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Hola, soy tu bot de registro de horas. Por favor, ingresa tu hora de entrada en formato HH.MM")
    return HORA_ENTRADA

# Registrar la hora de entrada
def hora_entrada(update: Update, context: CallbackContext) -> int:
    fecha = datetime.today().date().strftime("%Y-%m-%d")
    entrada_str = update.message.text
    try:
        # Convertir la hora de entrada
        entrada = datetime.strptime(entrada_str, "%H.%M").time()
        context.user_data['entrada_str'] = entrada_str
        context.user_data['entrada'] = datetime.combine(datetime.today().date(), entrada)
        context.user_data['fecha'] = fecha
        update.message.reply_text(f"Hora de entrada registrada: {entrada_str}. Ahora, por favor ingresa la hora de salida en formato HH.MM")
        return HORA_SALIDA
    except ValueError:
        update.message.reply_text("Formato incorrecto. Usa el formato HH.MM (por ejemplo, 08.30). Intenta de nuevo.")
        return HORA_ENTRADA

# Registrar la hora de salida y calcular total de horas
def hora_salida(update: Update, context: CallbackContext) -> int:
    salida_str = update.message.text
    try:
        # Convertir la hora de salida
        salida_time = datetime.strptime(salida_str, "%H.%M").time()
        salida = datetime.combine(datetime.today().date(), salida_time)
        entrada = context.user_data['entrada']
        entrada_str = context.user_data['entrada_str']
        fecha = context.user_data['fecha']

        # Manejar caso donde la salida es al día siguiente
        if salida < entrada:
            salida = salida.replace(day=salida.day + 1)

        # Calcular total de horas
        total_hrs = (salida - entrada).total_seconds() / 3600  # Convertir a horas

        # Actualizar el CSV
        df = cargar_csv()
        nueva_fila = pd.DataFrame({
            "Fecha": [fecha], 
            "Entrada": [entrada_str], 
            "Salida": [salida_str], 
            "Total Hrs": [round(total_hrs, 2)]
        })
        df = pd.concat([df, nueva_fila], ignore_index=True)
        guardar_csv(df)

        update.message.reply_text(f"Hora de salida registrada: {salida_str}. Total de horas trabajadas: {round(total_hrs, 2)} hrs.")
        return ConversationHandler.END
    except ValueError:
        update.message.reply_text("Formato incorrecto. Usa el formato HH.MM (por ejemplo, 17.45). Intenta de nuevo.")
        return HORA_SALIDA

# Función para cancelar la conversación
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Registro cancelado.")
    return ConversationHandler.END

# Función principal para iniciar el bot
def main():
    # Crea el Updater y el Dispatcher
    updater = Updater("7943538803:AAHk_cc6k696VcyjUK69k-Z0ehIaJ2Rhg3I", use_context=True)
    dispatcher = updater.dispatcher

    # Configuración del ConversationHandler
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            HORA_ENTRADA: [MessageHandler(Filters.text & ~Filters.command, hora_entrada)],
            HORA_SALIDA: [MessageHandler(Filters.text & ~Filters.command, hora_salida)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conversation_handler)

    # Iniciar el bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()