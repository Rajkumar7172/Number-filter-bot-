import telebot
import requests

# ====== अपने credentials भरो ======
BOT_TOKEN = "8073756056:AAH5hBs9DvVOwiaNc9foSsDKltCBc-V5_2A"
TWILIO_SID = "ACfcbaf27d63e33e24c9fffca172576111"
TWILIO_AUTH = "7f65cfc187987bf352c0eefa477c4307"
TWILIO_NUMBER = "whatsapp:+14155238886"  # Twilio sandbox number

bot = telebot.TeleBot(BOT_TOKEN)

def check_whatsapp(number):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json"
    data = {
        "To": f"whatsapp:{number}",
        "From": TWILIO_NUMBER,
        "Body": "test"
    }
    resp = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_AUTH))
    if resp.status_code == 201:
        return True
    return False

@bot.message_handler(content_types=['document'])
def handle_file(message):
    try:
        # File download
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        # Save local
        with open("numbers.txt", "wb") as f:
            f.write(downloaded_file)

        bot.reply_to(message, "📂 File received! Checking numbers...")

        # Read numbers
        with open("numbers.txt", "r") as f:
            numbers = f.read().splitlines()

        whatsapp_numbers = []
        for num in numbers:
            num = num.strip()
            if num.startswith("+") and check_whatsapp(num):
                whatsapp_numbers.append(num)

        # Save results
        with open("whatsapp_numbers.txt", "w") as f:
            f.write("\n".join(whatsapp_numbers))

        # Send back file
        with open("whatsapp_numbers.txt", "rb") as f:
            bot.send_document(message.chat.id, f)

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

@bot.message_handler(func=lambda m: True)
def echo(message):
    bot.reply_to(message, "📌 मुझे एक .txt file भेजो जिसमें numbers हों (country code के साथ)।")

bot.polling()
