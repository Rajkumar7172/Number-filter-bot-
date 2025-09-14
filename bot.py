# bot.py
import re
import csv
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters

# ====== CONFIG ======
TOKEN = "8203757475:AAG7255sxTDgsiRCv3Oenu5ce7js85KitD0"       # <-- अपना बोट टोकन डालें
OUTPUT_CSV = "found_numbers.csv"
FORWARD_CHAT_ID = None              # अगर रिपोर्ट किसी और chat में भेजनी है तो chat_id डालें, नहीं तो None
# ====================

# पैटर्न (इंडिया-फोकस) और generic fallback
INDIAN_PATTERN = re.compile(r'(?:\+91[\-\s]?|0)?[6-9]\d{9}')
GENERIC_PATTERN = re.compile(r'(\+?\d{1,3}[-\s.]?)?(?:\d[-\s.]?){5,14}\d')

def save_numbers(numbers, username, chat_id):
    path = Path(OUTPUT_CSV)
    exists = path.exists()
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow(["number","source_username","source_chat_id","timestamp"])
        ts = datetime.utcnow().isoformat() + "Z"
        for n in numbers:
            writer.writerow([n, username or "", chat_id, ts])

def normalize_number(item):
    # remove spaces, dashes, dots, parentheses
    s = re.sub(r'[\s\-\.\(\)]', '', item)
    # simple normalization: if 10 digit and starts with [6-9], keep as is; if starts with 0 remove leading zero and add +91
    if s.startswith("0") and len(s) == 11:
        s = s[1:]
    # optional: keep as-is, you can add country code normalization here
    return s

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("नमस्ते! मैं नंबर-filter bot हूँ — मैं मिलने वाले नंबर एक-एक करके भेजूंगा और CSV में सेव करूँगा।")

async def scan_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return

    text = msg.text if msg.text else (msg.caption if msg.caption else "")
    if not text:
        return

    # Find numbers
    found = INDIAN_PATTERN.findall(text)
    if not found:
        found = [m.group(0) for m in GENERIC_PATTERN.finditer(text)]

    # Normalize & unique per message
    cleaned = []
    seen = set()
    for item in found:
        norm = normalize_number(item)
        if norm and norm not in seen:
            seen.add(norm)
            cleaned.append(norm)

    if not cleaned:
        return

    # Save all numbers at once (with same timestamp)
    save_numbers(cleaned, msg.from_user.username if msg.from_user else None, msg.chat.id)

    # Send one-by-one replies
    total = len(cleaned)
    for idx, number in enumerate(cleaned, start=1):
        reply_text = f"Number {idx}/{total}: {number}"
        try:
            await msg.reply_text(reply_text)
        except Exception:
            # अगर reply नहीं जा पाए तो ignore
            pass

        # optional forward each to another chat (if set)
        if FORWARD_CHAT_ID:
            try:
                await context.bot.send_message(
                    chat_id=FORWARD_CHAT_ID,
                    text=f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC] From @{msg.from_user.username if msg.from_user else 'unknown'} in {msg.chat.title or msg.chat.id} — {number}"
                )
            except Exception:
                pass

async def get_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    path = Path(OUTPUT_CSV)
    if path.exists():
        await update.message.reply_document(document=str(path))
    else:
        await update.message.reply_text("कोई रिकॉर्ड नहीं मिला।")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("getcsv", get_csv))
    text_filter = filters.TEXT & (~filters.COMMAND)
    app.add_handler(MessageHandler(text_filter, scan_message))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()