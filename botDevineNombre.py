from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import random
import os
from dotenv import load_dotenv
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN=os.getenv('TOKEN')

etatJeu = {}

# --- Gestion du jeu ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userId = update.message.from_user.id
    etatJeu[userId] = {
        'nombreSecret': random.randint(1, 100),
        'tentativesRestantes': 5
    }
    await update.message.reply_text(
        "J'ai choisi un nombre entre 1 et 100. Tu as 5 chances pour le trouver !\nEt à chaque erreur tu as un nouveau indice."
    )

def estPremier(n: int):
    if n < 2:
        return False
    for i in range(2, int(n / 2 + 1)):
        if n % i == 0:
            return False
    return True

def donnerIndice(userId):
    nombreSecret = etatJeu[userId]['nombreSecret']
    tentatives = etatJeu[userId]['tentativesRestantes']
    if tentatives == 4:
        return 'premier indice: Le nombre est plus petit que 50 📉' if nombreSecret < 50 else 'premier indice: Le nombre est plus grand que 50 📈'
    elif tentatives == 3:
        return 'deuxième indice: Le nombre est pair' if nombreSecret % 2 == 0 else 'deuxième indice: Le nombre est impair'
    elif tentatives == 2:
        if nombreSecret % 2 != 0:
            return 'troisième indice: Le nombre est premier' if estPremier(nombreSecret) else 'troisième indice: Le nombre n\'est pas premier'
        else:
            return f'troisième indice: Le nombre se termine par {str(nombreSecret)[-1]}'
    elif tentatives == 1:
        number = [int(chiffre) for chiffre in str(nombreSecret)]
        return f'Quatrième et dernier indice: La somme des chiffres du nombre est {sum(number)}'

async def jouer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userId = update.message.from_user.id
    if userId not in etatJeu:
        await update.message.reply_text('Tape /start pour commencer une partie.')
        return

    try:
        proposition = int(update.message.text)
    except ValueError:
        await update.message.reply_text('Envoie un nombre valide.')
        return

    secretNumber = etatJeu[userId]['nombreSecret']
    if proposition == secretNumber:
        await update.message.reply_text('🎉 Bravo, tu as trouvé le nombre !')
        del etatJeu[userId]
    else:
        etatJeu[userId]['tentativesRestantes'] -= 1
        tentatives = etatJeu[userId]['tentativesRestantes']
        if tentatives == 0:
            await update.message.reply_text(f"❌ Perdu ! Le nombre était {secretNumber}.")
            del etatJeu[userId]
        else:
            indice = donnerIndice(userId)
            await update.message.reply_text(f'{indice} - Tentatives restantes: {tentatives}')

# --- Serveur HTTP minimal pour Render ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_dummy_server():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- Lancement du bot ---
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, jouer))
    print("Bot démarré avec polling... Appuie sur CTRL+C pour arrêter.")
    app.run_polling()
