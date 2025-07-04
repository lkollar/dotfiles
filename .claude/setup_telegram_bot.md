# Telegram Bot Setup for Claude Code Notifications

## Prerequisites

1. **Create a Telegram Bot**:
   - Open Telegram and search for `@BotFather`
   - Start a conversation and type `/newbot`
   - Follow the prompts to create your bot
   - Save the bot token (looks like `1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ`)

2. **Get Your Chat ID**:
   - Start a conversation with your new bot
   - Send any message to the bot
   - Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Look for the `chat` object and copy the `id` field

3. **No additional dependencies needed** - uses Python standard library only

## Configuration

Set these environment variables in `~/.env` (`.zshrc` will source it).

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

Then reload your shell:
```bash
source ~/.zshrc
```

## Testing

Test the notification system:
```bash
echo '{"type": "Stop"}' | python3 /home/lkollar/.claude/telegram_notifier.py
```

You should receive a notification on Telegram.
