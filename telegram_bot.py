import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from database import get_connection

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("telegram-bot")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 I am LLM Monitor Bot.\n"
        "I watch OpenRouter free models for you.\n\n"
        "Commands:\n"
        "/subscribe - Get alerts when models go down/up\n"
        "/unsubscribe - Stop alerts\n"
        "/status - Show current stats (TODO)"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_connection()
    try:
        conn.execute("INSERT OR IGNORE INTO subscribers (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        await update.message.reply_text("✅ Subscribed to alerts!")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Database error.")
    finally:
        conn.close()

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = get_connection()
    try:
        conn.execute("DELETE FROM subscribers WHERE chat_id = ?", (chat_id,))
        conn.commit()
        await update.message.reply_text("🔕 Unsubscribed.")
    except Exception as e:
        logger.error(e)
    finally:
        conn.close()

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # Query to get latest check for each model
        query = """
            SELECT m.id, m.is_vlm, c.success, c.latency_ms
            FROM models m
            LEFT JOIN checks c ON c.id = (
                SELECT id FROM checks WHERE model_id = m.id ORDER BY timestamp DESC LIMIT 1
            )
            WHERE m.is_active = 1
            ORDER BY c.success DESC, c.latency_ms ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            await update.message.reply_text("No models found in database.")
            return

        online = []
        offline = []
        for mid, is_vlm, success, latency in rows:
            icon = "👁️" if is_vlm else "💬"
            if success:
                online.append(f"{icon} `{mid}`: *{latency}ms*")
            else:
                offline.append(f"❌ `{mid}`")

        text = "📊 *Current Status*\n\n"
        if online:
            text += "*Online:*\n" + "\n".join(online) + "\n\n"
        if offline:
            text += "*Offline:*\n" + "\n".join(offline)
            
        text += f"\n\nTotal models monitored: {len(rows)}"
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Error fetching status.")
    finally:
        conn.close()

async def broadcast_loop(app):
    """Periodically checks DB for new notifications and sends them."""
    while True:
        await asyncio.sleep(5)
        conn = get_connection()
        try:
            # Get unsent notifications
            cursor = conn.cursor()
            cursor.execute("SELECT id, message FROM notification_queue WHERE sent = 0 ORDER BY id ASC")
            rows = cursor.fetchall()
            
            if not rows:
                continue

            # Get subscribers
            cursor.execute("SELECT chat_id FROM subscribers")
            subs = [r[0] for r in cursor.fetchall()]

            if not subs:
                # Mark as sent anyway so they don't pile up
                ids = [r[0] for r in rows]
                conn.execute(f"UPDATE notification_queue SET sent = 1 WHERE id IN ({','.join(map(str, ids))})")
                conn.commit()
                continue

            for msg_id, text in rows:
                for chat_id in subs:
                    try:
                        await app.bot.send_message(chat_id=chat_id, text=text)
                    except Exception as e:
                        logger.error(f"Failed to send to {chat_id}: {e}")
                
                # Mark as sent
                conn.execute("UPDATE notification_queue SET sent = 1 WHERE id = ?", (msg_id,))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
        finally:
            conn.close()

if __name__ == '__main__':
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        exit(1)

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('subscribe', subscribe))
    app.add_handler(CommandHandler('unsubscribe', unsubscribe))
    app.add_handler(CommandHandler('status', status))

    # Run broadcast loop in background
    loop = asyncio.get_event_loop()
    loop.create_task(broadcast_loop(app))

    app.run_polling()
