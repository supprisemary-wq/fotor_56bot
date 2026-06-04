import os
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from PIL import Image, ImageFilter, ImageOps

# Retrieve token from Render Environment Settings
TOKEN = os.getenv("TOKEN", "YOUR_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a welcome instruction message when /start is triggered."""
    welcome_text = (
        "🎨 **Welcome to Fotor - Your Graphic Design Assistant!** 🎨\n\n"
        "I am an automated image editing bot running directly in the background.\n\n"
        "📸 **How to use me:**\n"
        "Just send or forward me **any image** (as a photo or file), and I will present you with quick professional editing options instantly!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Intercept incoming photos and present processing options."""
    # Get the highest resolution version of the photo sent
    photo_file = await update.message.photo[-1].get_file()
    
    # Save the file ID in user data to process it during the callback
    context.user_data['edit_file_id'] = photo_file.file_id

    # Create inline design option buttons
    keyboard = [
        [InlineKeyboardButton("🌫️ Cinematic Background Blur", callback_data="blur")],
        [InlineKeyboardButton("🖤 Sleek Black & White", callback_data="monochrome")],
        [InlineKeyboardButton("📐 Flip Horizontal (Mirror Image)", callback_data="mirror")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✨ **Image Received!** Select a graphic design action below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def process_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the design selection from the user."""
    query = update.callback_query
    await query.answer()

    file_id = context.user_data.get('edit_file_id')
    if not file_id:
        await query.edit_message_text("❌ Session expired. Please send a new photo.")
        return

    await query.edit_message_text("⚙️ Processing your graphic asset...")

    try:
        # Download image into system memory
        tg_file = await context.bot.get_file(file_id)
        img_bytes = await tg_file.download_as_bytearray()
        
        # Load the image using Pillow library
        img = Image.open(io.BytesIO(img_bytes))
        
        action = query.data
        output_filename = "edited_asset.png"

        # Apply chosen design action
        if action == "blur":
            img = img.filter(ImageFilter.GaussianBlur(radius=6))
            caption_text = "🌫️ **Background Blur filter applied!**"
        elif action == "monochrome":
            img = ImageOps.grayscale(img)
            caption_text = "🖤 **Sleek Black & White filter applied!**"
        elif action == "mirror":
            img = ImageOps.mirror(img)
            caption_text = "📐 **Image mirrored horizontally!**"

        # Save the processed image back into memory buffer as PNG
        out_buffer = io.BytesIO()
        img.save(out_buffer, format="PNG")
        out_buffer.seek(0)

        # Send the finalized design asset back to the user
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=out_buffer,
            caption=f"{caption_text}\n\n🎯 _Optimized by Fotor_",
            parse_mode="Markdown"
        )

    except Exception as e:
        print(f"Design Engine Error: {str(e)}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="❌ An error occurred while processing your design asset. Please make sure it's a valid image."
        )

def main():
    """Start the Fotor background worker application loop."""
    application = Application.builder().token(TOKEN).build()

    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(process_button_click))

    # Run polling loop
    print("✅ Fotor Bot is actively running as a Graphic Design Background Worker...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
