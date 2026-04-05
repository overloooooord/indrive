"""
sync_bot_applications.py — Синхронизация заявок из Telegram-бота (Supabase)
в основную таблицу Application (Django).

Использование:
    python manage.py sync_bot_applications
    python manage.py sync_bot_applications --dry-run   # только показать, не сохранять
"""

from django.core.management.base import BaseCommand
from candidates.models import Application, BotApplication


class Command(BaseCommand):
    help = "Импортирует заявки из Supabase (bot) в Application (Django)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Показать что будет сделано, но не сохранять',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        if dry:
            self.stdout.write(self.style.WARNING("=== DRY RUN — без сохранения ===\n"))

        bot_apps = list(BotApplication.objects.all())
        total = len(bot_apps)
        self.stdout.write(f"Найдено заявок в боте: {total}")

        created = updated = skipped = 0

        for bot in bot_apps:
            # Пропускаем без имени
            if not bot.name:
                skipped += 1
                continue

            defaults = dict(
                # ── Личные данные ──
                name=bot.name or '',
                age=bot.age,
                city=bot.city or '',
                region=bot.region or '',
                school_type=bot.school_type or '',
                languages=bot.languages or [],
                telegram_username=bot.telegram_username or '',

                # ── Образование ──
                gpa=bot.gpa,
                gpa_raw=bot.gpa_raw or '',
                ielts_score=bot.ielts_score,
                ent_score=bot.ent_score,
                olympiads=bot.olympiads or [],
                courses=bot.courses or [],

                # ── Проекты ──
                projects=bot.projects or [],

                # ── Эссе ──
                essay=bot.essay_text or '',
                essay_nlp=bot.essay_nlp,

                # ── SLPI / Сценарии ──
                scenario_choices=bot.scenario_choices or {},
                fingerprint_display=bot.fingerprint_display,
                fingerprint_reliable=bot.fingerprint_reliable,
                timer_violations=bot.timer_violations or 0,

                # ── ML-результат ──
                scoring_result={
                    'prediction':    bot.score_prediction,
                    'confidence':    bot.score_confidence,
                    'probabilities': bot.score_probabilities,
                    'explanation':   bot.score_explanation,
                    'radar':         bot.score_radar,
                    'flags':         bot.score_flags,
                } if bot.score_prediction else None,

                # ── Метаданные ──
                source='bot',
                status='new',
            )

            if dry:
                obj = Application.objects.filter(telegram_id=bot.telegram_id).first()
                action = "UPDATE" if obj else "CREATE"
                self.stdout.write(f"  [{action}] {bot.name} (tg:{bot.telegram_id})")
                continue

            obj, was_created = Application.objects.update_or_create(
                telegram_id=bot.telegram_id,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        if not dry:
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ Готово: создано {created}, обновлено {updated}, пропущено {skipped}"
            ))
