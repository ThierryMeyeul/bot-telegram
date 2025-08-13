from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import random


TOKEN = '8231817887:AAE41IxavQvo-ibSYYkskIfl0SUNxWEp4TY'
etatJeu = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    userId = update.message.from_user.id
    print(userId)
    etatJeu[userId] = {
        'nombreSecret': random.randint(1, 100),
        'tentativesRestantes': 5
    }
    await update.message.reply_text('J\'ai choisi un nombre entre 1 et 100. Tu as 5 chances pour le trouver !\nEt à chaque erreur tu as un nouveau indice')


def estPremier(n: int):
    for i in range(2, int(n / 2 + 1)):
        if n % i == 0:
            return False
    return True

    
def donnerIndice(id):
    nombreSecret = etatJeu[id]['nombreSecret']
    tentatives = etatJeu[id]['tentativesRestantes']
    if tentatives == 4:
        if nombreSecret < 50:
            return 'premier indice: Le nombre est plus petit que 50 📉'
        else:
            return 'premier indice: Le nombre est plus grand que 50 📈'
    elif tentatives == 3:
        if nombreSecret % 2 == 0:
            return 'deuxième indice: Le nombre est un nombre pair'
        else:
            return 'deuxième indice: Le nombre est un nombre impair'
    elif tentatives == 2 and not nombreSecret % 2 == 0:
        if estPremier(nombreSecret):
            return 'troisième indice: Le nombre est un nombre premier'
        else :
            return 'troisième indice: Le nombre n\'est pas un nombre premier'
    elif tentatives == 2 and nombreSecret % 2 == 0:
        return f'troisième indice: Le nombre se termine par {(str(nombreSecret))[-1]}'
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
        tentatives =  etatJeu[userId]['tentativesRestantes']
        
        if tentatives == 0:
            await update.message.reply_text(f"❌ Perdu ! Le nombre était {secretNumber}.")
            del etatJeu[userId]
        else : 
            indice = donnerIndice(userId)
            await update.message.reply_text(f'{indice} - Tentatives restantes: {tentatives}')
    
    
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, jouer))
    print("Bot démarré... Appuie sur CTRL+C pour arrêter.")
    app.run_polling()