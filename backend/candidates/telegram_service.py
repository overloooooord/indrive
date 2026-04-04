import urllib.request
import urllib.parse
import json
import logging
from django.conf import settings
logger = logging.getLogger('candidates')
def notify_new_application(application):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_ids = getattr(settings, 'TELEGRAM_CHAT_IDS', [])
    if not token or token == 'YOUR_BOT_TOKEN_HERE':
        logger.warning(
            "Telegram не настроен: TELEGRAM_BOT_TOKEN не указан в .env. "
            "Уведомление не отправлено."
        )
        return
    if not chat_ids:
        logger.warning("Telegram CHAT_IDS пусты. Уведомление не отправлено.")
        return
    languages_str = ', '.join(application.languages) if application.languages else '—'
    text = (
        f"🆕 *Новая заявка!*\n\n"
        f"👤 *Имя:* {_escape_md(application.name)}\n"
        f"🏙 *Город:* {_escape_md(application.city)}\n"
        f"📍 *Регион:* {_escape_md(application.region)}\n"
        f"🌐 *Языки:* {_escape_md(languages_str)}\n"
        f"📱 *Telegram:* {_escape_md(application.telegram_username)}\n"
        f"⚽ *Спорт:* {_escape_md(application.sport or '—')}\n"
        f"📝 *Хобби:* {_escape_md(application.hobbies[:100] or '—')}\n"
        f"\n📅 *Дата:* {application.created_at.strftime('%d.%m.%Y %H:%M') if application.created_at else '—'}"
    )
    for chat_id in chat_ids:
        try:
            _send_message(token, chat_id, text)
            logger.info(f"Telegram уведомление отправлено в chat {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки Telegram в chat {chat_id}: {e}")
def notify_new_candidate(candidate):
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
    chat_ids = getattr(settings, 'TELEGRAM_CHAT_IDS', [])
    if not token or token == 'YOUR_BOT_TOKEN_HERE' or not chat_ids:
        logger.warning("Telegram не настроен, уведомление не отправлено.")
        return
    gpa = candidate.profile_data.get('education', {}).get('gpa', '—')
    projects = len(candidate.profile_data.get('experience', {}).get('projects', []))
    text = (
        f"🆕 *Новый кандидат зарегистрирован!*\n\n"
        f"👤 *Имя:* {_escape_md(candidate.name)}\n"
        f"🎂 *Возраст:* {candidate.age}\n"
        f"🏙 *Город:* {_escape_md(candidate.city or '—')}\n"
        f"📍 *Регион:* {_escape_md(candidate.region or '—')}\n"
        f"🎓 *GPA:* {gpa}\n"
        f"🚀 *Проектов:* {projects}\n"
        f"🏫 *Тип школы:* {_escape_md(candidate.school_type or '—')}\n"
    )
    for chat_id in chat_ids:
        try:
            _send_message(token, chat_id, text)
        except Exception as e:
            logger.error(f"Failed to send Telegram to {chat_id}: {e}")
def _escape_md(text: str) -> str:
    if not text:
        return '—'
    for char in ('_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!'):
        text = text.replace(char, f'\\{char}')
    return text
def _send_message(token: str, chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'Markdown',
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            if not result.get('ok'):
                logger.warning(f"Telegram API error: {result}")
    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        raise
