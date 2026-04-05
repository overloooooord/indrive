import asyncio
import logging
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
from datetime import datetime
from keyboards import kb_school
from helpers import save_to_json

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from states import (
    ConsentState, PersonalState, EducationState,
    ExperienceState, EssayState, ScenarioState, FileUploadState
)
from keyboards import (
    kb_start, kb_about_back, kb_consent, kb_yes_skip,
    kb_olympiad_level, kb_prize, kb_add_more, kb_completed,
    kb_project_type, kb_role, kb_failure, kb_continued,
    kb_go, kb_upload_file, kb_done,
    kb_no_ielts, kb_no_ent, kb_skip_cert
)
from database import get_or_create_application, update_application, get_application
from helpers import (
    validate_name, validate_age, validate_city, validate_year,
    validate_team_size, validate_essay, extract_gpa, build_summary
)
from config import MAX_OLYMPIADS, MAX_COURSES, MAX_PROJECTS, SCENARIO_TIMER_SECONDS
from scenario_engine import compute_fingerprint

router = Router()
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# SCENARIO DEFINITIONS
# Full 25-question branching tree (InVision U SLPI bank)
# Each candidate sees: 5 entry questions + 5 branch questions = 10 total
# ──────────────────────────────────────────────

SCENARIOS = {
    "sc1": {
        "entry": {
            "text": (
                "Ты отвечаешь за школьное мероприятие. За 3 дня до события "
                "главный организатор выбыл — заболел. Всё держалось на нём. "
                "Что делаешь?"
            ),
            "options": {
                "A": "Беру всё на себя — справлюсь",
                "B": "Собираю команду и распределяю задачи",
                "C": "Срочно ищу замену организатору",
                "D": "Сообщаю куратору / классному руководителю",
            }
        },
        "branches": {
            "A": {
                "text": (
                    "К вечеру ты понимаешь, что не успеваешь. "
                    "Задач слишком много, до события 2 дня. Что дальше?"
                ),
                "options": {
                    "A": "Работаю всю ночь — сдаться нельзя",
                    "B": "Иду к команде за помощью — надо было сразу",
                    "C": "Прошу куратора сдвинуть дату мероприятия",
                    "D": "Упрощаю программу — делаю только главное",
                }
            },
            "B": {
                "text": (
                    "Один человек в команде не справляется со своей частью. "
                    "До мероприятия 2 дня. Что делаешь?"
                ),
                "options": {
                    "A": "Оставляю — каждый заслуживает шанс",
                    "B": "Заменяю — результат команды важнее",
                    "C": "Сначала говорю с ним напрямую — узнаю причину",
                    "D": "Тихо перераспределяю его задачи на других",
                }
            },
            "C": {
                "text": (
                    "Новый организатор согласен помочь, но просит больше бюджета — "
                    "иначе не берётся. Бюджет фиксирован. Что делаешь?"
                ),
                "options": {
                    "A": "Соглашаюсь — найду деньги где-нибудь",
                    "B": "Отказываю — буду искать другого",
                    "C": "Торгуюсь — предлагаю что-то нематериальное взамен",
                    "D": "Возвращаюсь к идее сделать всё силами команды",
                }
            },
            "D": {
                "text": (
                    "Куратор отвечает: «Это ваша ответственность — разбирайтесь сами». "
                    "Что делаешь?"
                ),
                "options": {
                    "A": "Принимаю — иду и сам(а) решаю проблему",
                    "B": "Объясняю, что один(а) не справлюсь — прошу минимального участия",
                    "C": "Предлагаю конкретный план и прошу только одобрение",
                    "D": "Нахожу другого взрослого, который может помочь",
                }
            },
        }
    },

    "sc2": {
        "entry": {
            "text": (
                "В вашем проекте двое участников поссорились. "
                "Они отказываются работать вместе. Работа стоит. "
                "Ты лидер. Что делаешь?"
            ),
            "options": {
                "A": "Говорю им решить это самостоятельно — взрослые люди",
                "B": "Разговариваю с каждым отдельно — сначала выслушиваю",
                "C": "Собираю всех троих — решаем открыто",
                "D": "Перераспределяю задачи так, чтобы они не пересекались",
            }
        },
        "branches": {
            "A": {
                "text": (
                    "Конфликт не утихает. Уже неделя. "
                    "Проект под угрозой срыва. Что теперь?"
                ),
                "options": {
                    "A": "Всё же вмешиваюсь — провожу разговор с каждым",
                    "B": "Ставлю ультиматум: мир или выходите из команды",
                    "C": "Временно беру их задачи на себя",
                    "D": "Иду к куратору — признаю, что не справляюсь",
                }
            },
            "B": {
                "text": (
                    "После разговора один согласился двигаться дальше. "
                    "Второй по-прежнему держит обиду — не идёт на контакт. "
                    "Что делаешь?"
                ),
                "options": {
                    "A": "Даю время — обиды проходят сами",
                    "B": "Снова говорю лично — ищу корень проблемы",
                    "C": "Меняю его роль в проекте — меньше пересечений",
                    "D": "Признаю его чувства публично перед командой",
                }
            },
            "C": {
                "text": (
                    "На общем разговоре один из них начинает говорить резко. "
                    "Напряжение растёт. Остальные молчат. Как реагируешь?"
                ),
                "options": {
                    "A": "Останавливаю: «Давайте без повышенного тона»",
                    "B": "Даю выговориться — пусть скажет всё",
                    "C": "Переключаю на задачи: «Вернёмся к проекту»",
                    "D": "Делаю паузу — предлагаю продолжить через час",
                }
            },
            "D": {
                "text": (
                    "После перераспределения один из них чувствует себя отодвинутым. "
                    "Он(а) уходит из проекта. Что делаешь?"
                ),
                "options": {
                    "A": "Принимаю решение — это его право",
                    "B": "Иду за ним(ей) — пробую поговорить лично",
                    "C": "Ищу нового участника и двигаюсь дальше",
                    "D": "Признаю публично, что допустил(а) ошибку в управлении",
                }
            },
        }
    },

    "sc3": {
        "entry": {
            "text": (
                "У тебя есть идея, которая улучшит ваш школьный проект. "
                "Но классный руководитель против — «делайте как всегда». "
                "Что делаешь?"
            ),
            "options": {
                "A": "Принимаю отказ — не стоит создавать конфликт",
                "B": "Прошу объяснить причину отказа",
                "C": "Реализую идею в рамках того, что уже разрешено",
                "D": "Иду выше — к завучу или директору",
            }
        },
        "branches": {
            "A": {
                "text": (
                    "Проект прошёл. Ты видишь: твоя идея сработала бы лучше. "
                    "Другие тоже это заметили. Что дальше?"
                ),
                "options": {
                    "A": "Ничего — в следующий раз промолчу",
                    "B": "Готовлю аргументы — предложу снова на следующем проекте",
                    "C": "Реализую идею самостоятельно в другом месте",
                    "D": "Собираю мнения команды и иду с общим запросом",
                }
            },
            "B": {
                "text": (
                    "Учитель объяснил причину. Ты не согласен(а), но логику понял(а). "
                    "Что делаешь?"
                ),
                "options": {
                    "A": "Принимаю — доверяю опыту учителя",
                    "B": "Предлагаю компромисс — частично изменить подход",
                    "C": "Прошу разрешения протестировать идею в маленьком масштабе",
                    "D": "Остаюсь при своём — буду доказывать делом, не словами",
                }
            },
            "C": {
                "text": (
                    "Другие участники заметили твой подход. "
                    "Они хотят сделать так же. Учитель видит результат. "
                    "Что делаешь?"
                ),
                "options": {
                    "A": "Рассказываю всем, как это работает — делюсь открыто",
                    "B": "Предлагаю оформить это как официальное улучшение",
                    "C": "Отхожу в сторону — пусть сами разбираются",
                    "D": "Предлагаю создать небольшую группу для внедрения",
                }
            },
            "D": {
                "text": (
                    "Завуч тоже отказал — поддержал учителя. "
                    "Идея заблокирована на двух уровнях. Что делаешь?"
                ),
                "options": {
                    "A": "Принимаю — система решила, уважаю решение",
                    "B": "Прошу встречу с обоими — хочу показать конкретные аргументы",
                    "C": "Реализую идею вне школьного контекста — в личном проекте",
                    "D": "Нахожу союзников среди одноклассников или родителей",
                }
            },
        }
    },

    "sc4": {
        "entry": {
            "text": (
                "Участник твоей команды провалил важную часть работы. "
                "Он(а) чувствует себя ужасно и хочет выйти из проекта. "
                "Что делаешь?"
            ),
            "options": {
                "A": "Принимаю решение — его право уйти",
                "B": "Разговариваю с ним(ей) — хочу понять, что случилось",
                "C": "Перераспределяю задачи, чтобы снизить его(её) нагрузку",
                "D": "Прошу команду публично поддержать его(её)",
            }
        },
        "branches": {
            "A": {
                "text": (
                    "Команда расстроена. Несколько человек считают, "
                    "что ты должен(на) был(а) его удержать. Что делаешь?"
                ),
                "options": {
                    "A": "Объясняю команде своё решение — почему принял(а) его уход",
                    "B": "Всё же иду к ушедшему — пробую поговорить сейчас",
                    "C": "Признаю, что, возможно, стоило поступить иначе",
                    "D": "Фокусирую команду на задачах — сейчас не время для разбора",
                }
            },
            "B": {
                "text": (
                    "Выясняется: провал был из-за проблем дома. "
                    "Он(а) боится подвести снова. Как реагируешь?"
                ),
                "options": {
                    "A": "Предлагаю взять паузу — вернуться, когда будет готов(а)",
                    "B": "Даю задачу попроще — чтобы восстановить уверенность",
                    "C": "Говорю честно: «Мы с тобой, что бы ни случилось»",
                    "D": "Предлагаю вместе поговорить с куратором",
                }
            },
            "C": {
                "text": (
                    "Участник остался. Но другие в команде недовольны: "
                    "«Почему ему меньше задач? Это несправедливо». Что делаешь?"
                ),
                "options": {
                    "A": "Объясняю команде ситуацию — без лишних деталей",
                    "B": "Восстанавливаю нагрузку — справедливость важнее",
                    "C": "Даю команде высказаться — слушаю без защиты",
                    "D": "Прошу всех временно взять чуть больше — объясняю зачем",
                }
            },
            "D": {
                "text": (
                    "После публичной поддержки участник остался. "
                    "Через неделю снова не справляется. Ситуация повторяется. "
                    "Что делаешь?"
                ),
                "options": {
                    "A": "Разговариваю снова — ищу системную причину",
                    "B": "Меняю его роль принципиально — другой тип задач",
                    "C": "Честно говорю: «Вижу паттерн. Нужно что-то изменить»",
                    "D": "Подключаю куратора — это уже за пределами моей роли",
                }
            },
        }
    },

    "sc5": {
        "entry": {
            "text": (
                "Два проекта, в которых ты лидер, пересеклись по срокам. "
                "Нужно выбрать, куда вкладывать больше сил. "
                "Оба важны для тебя. Что делаешь?"
            ),
            "options": {
                "A": "Выбираю более важный и фокусируюсь только на нём",
                "B": "Пытаюсь вести оба — на максимуме усилий",
                "C": "Ищу, кто может взять один из проектов",
                "D": "Честно говорю обеим командам о ситуации",
            }
        },
        "branches": {
            "A": {
                "text": (
                    "Команда второго проекта чувствует себя брошенной. "
                    "Несколько человек говорят это тебе напрямую. Что делаешь?"
                ),
                "options": {
                    "A": "Объясняю причину выбора честно",
                    "B": "Нахожу время хотя бы для ключевых моментов второго проекта",
                    "C": "Предлагаю кому-то из них взять лидерство",
                    "D": "Признаю вслух, что взял(а) на себя слишком много",
                }
            },
            "B": {
                "text": (
                    "Через 10 дней качество в обоих проектах падает. "
                    "Команды это замечают. Что делаешь?"
                ),
                "options": {
                    "A": "Продолжаю — лучше плохо, чем бросить",
                    "B": "Признаю и делаю выбор в пользу одного",
                    "C": "Прошу команды взять на себя больше ответственности",
                    "D": "Открыто говорю кураторам обоих проектов о ситуации",
                }
            },
            "C": {
                "text": (
                    "Человек, которому ты передал(а) проект, справляется хуже, "
                    "чем ты ожидал(а). Команда недовольна. Что делаешь?"
                ),
                "options": {
                    "A": "Возвращаюсь и помогаю — объясняю, как делал(а) сам(а)",
                    "B": "Даю ему(ей) ещё время — это его(её) опыт, не мой",
                    "C": "Предлагаю работать вместе на ключевых этапах",
                    "D": "Нахожу другого человека на эту роль",
                }
            },
            "D": {
                "text": (
                    "Одна из команд предлагает объединить два проекта в один. "
                    "Ты видишь риски — разные цели, разные люди. Что делаешь?"
                ),
                "options": {
                    "A": "Соглашаюсь — совместное решение команды важнее моих опасений",
                    "B": "Выдвигаю условия объединения — только если...",
                    "C": "Предлагаю сначала пилот — один совместный этап, потом решим",
                    "D": "Отказываюсь и объясняю риски — честно, не уклоняясь",
                }
            },
        }
    },
}

SCENARIO_ORDER = ["sc1", "sc2", "sc3", "sc4", "sc5"]


# ──────────────────────────────────────────────
# SCENARIO KEYBOARD BUILDER
# ──────────────────────────────────────────────

def kb_scenario(sc_id: str, phase: str) -> InlineKeyboardMarkup:
    """
    sc_id: e.g. "sc1", "sc2", ...
    phase: "entry" or the branch letter chosen at entry ("A"/"B"/"C"/"D")
    """
    if phase == "entry":
        q = SCENARIOS[sc_id]["entry"]
    else:
        q = SCENARIOS[sc_id]["branches"][phase]

    buttons = []
    for letter, label in q["options"].items():
        # callback_data format: "ans_{sc_id}_{phase}_{letter}"
        # e.g. "ans_sc1_entry_B" or "ans_sc1_B_C"
        buttons.append([
            InlineKeyboardButton(
                text=f"{letter}. {label}",
                callback_data=f"ans_{sc_id}_{phase}_{letter}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_question_text(sc_id: str, phase: str) -> str:
    if phase == "entry":
        return SCENARIOS[sc_id]["entry"]["text"]
    return SCENARIOS[sc_id]["branches"][phase]["text"]


# ──────────────────────────────────────────────
# BLOCK 1 — Welcome
# ──────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await get_or_create_application(message.from_user.id, message.from_user.username)
    await update_application(
        message.from_user.id,
        funnel_stage="started",
        start_timestamp=datetime.utcnow()
    )
    await message.answer(
        "👋 Привет! Я помогу тебе подать заявку в *InVision U*.\n\n"
        "InVision U — университет с полными грантами от inDrive.\n"
        "Здесь учатся те, кто хочет менять мир вокруг себя —\n"
        "не обязательно с медалями и олимпиадами.\n\n"
        "Нам важно не только то, чего ты уже добился(лась) —\n"
        "а то, как ты думаешь, действуешь и растёшь.",
        parse_mode="Markdown"
    )
    await message.answer(
        "Анкета займёт около 20–25 минут.\n\n"
        "Из чего она состоит:\n"
        "— Несколько вопросов о тебе и твоём опыте\n"
        "— Один текстовый вопрос (эссе) — своими словами\n"
        "— Короткие сценарии-ситуации (там нет правильных ответов)\n\n"
        "Лучше пройти за один раз — можно сохранить прогресс,\n"
        "но сценарии нельзя перезапустить.",
        reply_markup=kb_start(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "about")
async def about_invision(callback: CallbackQuery):
    await callback.message.edit_text(
        "*InVision U* — образовательная программа от inDrive\n"
        "для молодых людей 16–25 лет из Казахстана.\n\n"
        "✦ Полный грант: обучение, проживание, менторы\n"
        "✦ Отбор по потенциалу, а не по оценкам\n"
        "✦ Фокус: лидерство, предпринимательство, социальные изменения",
        reply_markup=kb_about_back(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "start_app")
async def start_app(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "⚠️ *Прежде чем начать — важная информация о твоих данных.*\n\n"
        "Мы будем собирать:\n"
        "• Имя, возраст, город — для идентификации заявки\n"
        "• Опыт, проекты, оценки — для оценки потенциала\n"
        "• Ответы на вопросы и сценарии — для анализа мышления\n"
        "• Текст эссе — для оценки мотивации и аутентичности\n\n"
        "Как мы работаем с данными:\n"
        "— Хранятся только на серверах InVision U\n"
        "— Не передаются третьим лицам\n"
        "— Не используются для рекламы\n"
        "— Решение принимает живой человек, не автомат\n\n"
        "Отозвать согласие: privacy@invisionu.kz",
        parse_mode="Markdown"
    )
    await callback.message.answer(
        "Ты согласен(а) на сбор и обработку своих данных\n"
        "для участия в отборе InVision U?",
        reply_markup=kb_consent()
    )
    await state.set_state(ConsentState.waiting)
    await callback.answer()


# ──────────────────────────────────────────────
# BLOCK 2 — Consent
# ──────────────────────────────────────────────

@router.callback_query(ConsentState.waiting, F.data == "consent_yes")
async def consent_yes(callback: CallbackQuery, state: FSMContext):
    await update_application(
        callback.from_user.id,
        consent_given=True,
        consent_timestamp=datetime.utcnow(),
        funnel_stage="consented"
    )
    await callback.message.edit_text("✅ Согласие получено. Начинаем!")
    await ask_name(callback.message, state)
    await callback.answer()


@router.callback_query(ConsentState.waiting, F.data == "consent_no")
async def consent_no(callback: CallbackQuery, state: FSMContext):
    await update_application(callback.from_user.id, funnel_stage="consent_declined", consent_given=False)
    await callback.message.edit_text(
        "Всё понимаем. Без согласия мы не можем принять заявку.\n\n"
        "Если передумаешь — напиши /start, начнём заново.\n"
        "Вопросы: privacy@invisionu.kz"
    )
    await state.clear()
    await callback.answer()


# ──────────────────────────────────────────────
# BLOCK 3 — Personal Data
# ──────────────────────────────────────────────

async def ask_name(message: Message, state: FSMContext):
    await message.answer("*Блок 1 из 5 — Личные данные*\n\nКак тебя зовут?\nНапиши имя и фамилию.", parse_mode="Markdown")
    await state.set_state(PersonalState.name)


@router.message(PersonalState.name)
async def process_name(message: Message, state: FSMContext):
    if not validate_name(message.text):
        await message.answer("Напиши имя буквами — без цифр и символов. Например: Асель Нурова")
        return
    await update_application(message.from_user.id, name=message.text.strip())
    await message.answer("Сколько тебе лет?")
    await state.set_state(PersonalState.age)


@router.message(PersonalState.age)
async def process_age(message: Message, state: FSMContext):
    age = validate_age(message.text)
    if age is None:
        await message.answer("Введи число от 14 до 25. Например: 17")
        return
    await update_application(message.from_user.id, age=age)
    await message.answer("Из какого ты города или посёлка?")
    await state.set_state(PersonalState.city)


@router.message(PersonalState.city)
async def process_city(message: Message, state: FSMContext):
    await update_application(message.from_user.id, city=message.text)
    await state.set_state(PersonalState.region)
    await message.answer("В каком регионе ты живешь? (например, Область или Край)")


@router.message(PersonalState.region)
async def process_region(message: Message, state: FSMContext):
    await update_application(message.from_user.id, region=message.text, funnel_stage="personal_done")
    await state.set_state(EducationState.school_type)
    await message.answer("Выбери тип твоего учебного заведения:", reply_markup=kb_school)


# ──────────────────────────────────────────────
# BLOCK 4 — Education
# ──────────────────────────────────────────────

@router.callback_query(EducationState.school_type, F.data.startswith("school:"))
async def process_school(callback: CallbackQuery, state: FSMContext):
    school_val = callback.data.split(":")[1]
    await update_application(callback.from_user.id, school_type=school_val)
    await state.set_state(EducationState.languages)
    await callback.message.edit_text("Какие языки ты знаешь? Перечисли через запятую (например: Русский, Английский, Казахский)")


@router.message(EducationState.languages)
async def process_languages(message: Message, state: FSMContext):
    langs = [lang.strip() for lang in message.text.split(",")]
    await update_application(message.from_user.id, languages=langs)

    await ask_gpa(message, state)

async def ask_gpa(message: Message, state: FSMContext):
    await message.answer(
        "*Блок 2 из 5 — Образование*\n\n"
        "Какой у тебя средний балл за последний учебный год?\n\n"
        "Укажите его по казахстанской системе оценивания — числом от 1 до 5 (например: 4.2).\n"
        "Если вы учились по другой системе (например, 100-балльная и т.д.), переведите свой средний балл в казахстанскую шкалу (от 1 до 5)",
        parse_mode="Markdown"
    )
    await state.set_state(EducationState.gpa)


@router.message(EducationState.gpa)
async def process_gpa(message: Message, state: FSMContext):
    gpa_value = extract_gpa(message.text)

    if gpa_value is None:
        await message.answer(
            "Ошибка! Введи средний балл числом от 1 до 5.\n"
            "Пример: 4.2 или 5"
        )
        return  

    await update_application(message.from_user.id, gpa=gpa_value)
    
    await ask_ielts(message, state)


async def ask_ielts(message: Message, state: FSMContext):
    await message.answer(
        "📈 **Ваш балл IELTS**\n\n"
        "Пожалуйста, введите ваш общий балл (от 0 до 9.0).\n"
        "Если вы не сдавали этот тест, нажмите кнопку «Пропустить».",
        reply_markup=kb_no_ielts()
    )
    await state.set_state(EducationState.ielts_score)


@router.message(EducationState.ielts_score)
async def process_ielts_score(message: Message, state: FSMContext):
    raw = message.text.strip().replace(",", ".")
    try:
        score = float(raw)
        if not (0.0 <= score <= 9.0):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введите корректное число от 0 до 9. Например: 7.5")
        return
    await update_application(message.from_user.id, ielts_score=score)
    await state.update_data(last_score=score)
    
    await message.answer(
        f"✅ Балл {score} сохранен.\n\n"
        "📎 Теперь, пожалуйста, **прикрепите ваш сертификат IELTS** (фото или PDF-файл).",
        reply_markup=kb_skip_cert()
    )
    await state.set_state(EducationState.ielts_doc)


@router.callback_query(EducationState.ielts_score, F.data == "no_ielts")
async def no_ielts(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👌 IELTS пропущен. Переходим к ЕНТ.")
    await ask_ent(callback.message, state)
    await callback.answer()

@router.message(EducationState.ielts_doc, F.document | F.photo)
async def handle_ielts_doc(message: Message, state: FSMContext):
    await save_file_logic(message, "IELTS Certificate")
    await message.answer("✅ Сертификат IELTS успешно загружен.")
    await ask_ent(message, state)

@router.callback_query(EducationState.ielts_doc, F.data == "skip_cert")
async def skip_ielts_doc(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Ок, продолжим без файла.")
    await ask_ent(callback.message, state)
    await callback.answer()


async def ask_ent(message: Message, state: FSMContext):
    await message.answer(
        "🎓 **Ваш балл ЕНТ**\n\n"
        "Введите ваш балл (от 0 до 140).\n"
        "Если вы не сдавали ЕНТ, нажмите «Пропустить».",
        reply_markup=kb_no_ent() 
    )
    await state.set_state(EducationState.ent_score)


@router.message(EducationState.ent_score)
async def process_ent_score(message: Message, state: FSMContext):
    raw = message.text.strip()
    try:
        score = int(raw)
        if not (0 <= score <= 140):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите целое число от 0 до 140. Например: 120")
        return

    await update_application(message.from_user.id, ent_score=score)
    
    await message.answer(
        f"✅ Балл {score} записан.\n\n"
        "📎 Прикрепите **скриншот или сертификат ЕНТ**.",
        reply_markup=kb_skip_cert()
    )
    await state.set_state(EducationState.ent_doc)


@router.callback_query(EducationState.ent_score, F.data == "no_ent")
async def no_ent(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👌 ЕНТ пропущен.")
    await after_certs(callback.message, state, callback.from_user.id)
    await callback.answer()

@router.message(EducationState.ent_doc, F.document | F.photo)
async def handle_ent_doc(message: Message, state: FSMContext):
    await save_file_logic(message, "ENT Certificate")
    await message.answer("✅ Сертификат ЕНТ успешно загружен.")
    await after_certs(message, state, message.from_user.id)

@router.callback_query(EducationState.ent_doc, F.data == "skip_cert")
async def skip_ent_doc(callback: CallbackQuery, state: FSMContext):
    await after_certs(callback.message, state, callback.from_user.id)
    await callback.answer()

async def save_file_logic(message: Message, category: str):
    file_info = {"category": category}
    if message.document:
        file_info.update({
            "type": "document",
            "file_id": message.document.file_id,
            "file_name": message.document.file_name,
        })
    elif message.photo:
        photo = message.photo[-1]
        file_info.update({
            "type": "photo",
            "file_id": photo.file_id,
        })
    
    app = await get_application(message.from_user.id)
    files = list(app.uploaded_files or [])
    files.append(file_info)
    await update_application(message.from_user.id, uploaded_files=files)

async def after_certs(message: Message, state: FSMContext, user_id: int):
    await update_application(user_id, funnel_stage="education_done")
    await message.answer(
        "🏆 **Олимпиады и конкурсы**\n\n"
        "Участвовал(а) ли ты в республиканских или международных олимпиадах?",
        reply_markup=kb_yes_skip()
    )
    await state.set_state(EducationState.olympiad_filter)


# ── Olympiads ──

@router.callback_query(EducationState.olympiad_filter, F.data == "yes")
async def olympiad_yes(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Напиши предмет олимпиады.\nНапример: Математика, Биология, Робототехника")
    await state.set_state(EducationState.olympiad_subject)
    await callback.answer()


@router.callback_query(EducationState.olympiad_filter, F.data == "skip")
async def olympiad_skip(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Олимпиады пропущены.")
    await ask_courses(callback.message, state)
    await callback.answer()


@router.message(EducationState.olympiad_subject)
async def process_olympiad_subject(message: Message, state: FSMContext):
    await state.update_data(current_olympiad={"subject": message.text.strip()})
    await message.answer("В каком году это было?")
    await state.set_state(EducationState.olympiad_year)


@router.message(EducationState.olympiad_year)
async def process_olympiad_year(message: Message, state: FSMContext):
    year = validate_year(message.text)
    if year is None:
        await message.answer("Введи год от 2018 до 2026. Например: 2023")
        return
    data = await state.get_data()
    olympiad = data.get("current_olympiad", {})
    olympiad["year"] = year
    await state.update_data(current_olympiad=olympiad)
    await message.answer("Какой уровень?", reply_markup=kb_olympiad_level())
    await state.set_state(EducationState.olympiad_level)


@router.callback_query(EducationState.olympiad_level, F.data.startswith("level_"))
async def process_olympiad_level(callback: CallbackQuery, state: FSMContext):
    level = callback.data.replace("level_", "")
    data = await state.get_data()
    olympiad = data.get("current_olympiad", {})
    olympiad["level"] = level
    await state.update_data(current_olympiad=olympiad)
    await callback.message.edit_text("Ты занял(а) призовое место?", reply_markup=kb_prize())
    await state.set_state(EducationState.olympiad_prize)
    await callback.answer()


@router.callback_query(EducationState.olympiad_prize, F.data.in_(["prize_yes", "prize_no"]))
async def process_olympiad_prize(callback: CallbackQuery, state: FSMContext):
    prize = callback.data == "prize_yes"
    data = await state.get_data()
    olympiad = data.get("current_olympiad", {})
    olympiad["prize"] = prize

    app = await get_application(callback.from_user.id)
    olympiads = list(app.olympiads or [])
    olympiads.append(olympiad)
    await update_application(callback.from_user.id, olympiads=olympiads, funnel_stage="olympiads_done")

    count = len(olympiads)
    if count >= MAX_OLYMPIADS:
        await callback.message.edit_text(f"✅ Олимпиада добавлена (достигнут лимит {MAX_OLYMPIADS}).")
        await ask_courses(callback.message, state)
    else:
        await callback.message.edit_text(
            f"✅ Олимпиада добавлена ({count} из {MAX_OLYMPIADS}).\nДобавить ещё?",
            reply_markup=kb_add_more()
        )
        await state.set_state(EducationState.olympiad_loop)
    await callback.answer()


@router.callback_query(EducationState.olympiad_loop, F.data == "add_more")
async def olympiad_add_more(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Напиши предмет следующей олимпиады.")
    await state.set_state(EducationState.olympiad_subject)
    await callback.answer()


@router.callback_query(EducationState.olympiad_loop, F.data == "continue")
async def olympiad_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Олимпиады записаны ✅")
    await ask_courses(callback.message, state)
    await callback.answer()


# ── Courses ──

async def ask_courses(message: Message, state: FSMContext):
    await message.answer(
        "Проходил(а) ли ты онлайн-курсы или дополнительное обучение вне школы?\n"
        "Coursera, Stepik, YouTube-курсы, очные тренинги — всё считается.",
        reply_markup=kb_yes_skip()
    )
    await state.set_state(EducationState.course_filter)


@router.callback_query(EducationState.course_filter, F.data == "yes")
async def course_yes(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Как называется курс? Напиши коротко.\nНапример: Python basics, Курс по лидерству"
    )
    await state.set_state(EducationState.course_name)
    await callback.answer()


@router.callback_query(EducationState.course_filter, F.data == "skip")
async def course_skip(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Курсы пропущены.")
    await start_experience_block(callback.message, state)
    await callback.answer()


@router.message(EducationState.course_name)
async def process_course_name(message: Message, state: FSMContext):
    await state.update_data(current_course={"name": message.text.strip()})
    await message.answer("Где проходил(а)? Напиши платформу или место.\nНапример: Stepik, Coursera, очно в школе")
    await state.set_state(EducationState.course_platform)


@router.message(EducationState.course_platform)
async def process_course_platform(message: Message, state: FSMContext):
    data = await state.get_data()
    course = data.get("current_course", {})
    course["platform"] = message.text.strip()
    await state.update_data(current_course=course)
    await message.answer("В каком году?")
    await state.set_state(EducationState.course_year)


@router.message(EducationState.course_year)
async def process_course_year(message: Message, state: FSMContext):
    year = validate_year(message.text)
    if year is None:
        await message.answer("Введи год от 2018 до 2026.")
        return
    data = await state.get_data()
    course = data.get("current_course", {})
    course["year"] = year
    await state.update_data(current_course=course)
    await message.answer("Ты завершил(а) этот курс?", reply_markup=kb_completed())
    await state.set_state(EducationState.course_completed)


@router.callback_query(EducationState.course_completed, F.data.in_(["completed_yes", "completed_no"]))
async def process_course_completed(callback: CallbackQuery, state: FSMContext):
    completed = callback.data == "completed_yes"
    data = await state.get_data()
    course = data.get("current_course", {})
    course["completed"] = completed

    app = await get_application(callback.from_user.id)
    courses = list(app.courses or [])
    courses.append(course)
    await update_application(callback.from_user.id, courses=courses, funnel_stage="cources_done")

    count = len(courses)
    if count >= MAX_COURSES:
        await callback.message.edit_text(f"✅ Курс добавлен (лимит {MAX_COURSES}).")
        await start_experience_block(callback.message, state)
    else:
        await callback.message.edit_text(
            f"✅ Курс добавлен ({count} из {MAX_COURSES}).\nДобавить ещё?",
            reply_markup=kb_add_more()
        )
        await state.set_state(EducationState.course_loop)
    await callback.answer()


@router.callback_query(EducationState.course_loop, F.data == "add_more")
async def course_add_more(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Название следующего курса?")
    await state.set_state(EducationState.course_name)
    await callback.answer()


@router.callback_query(EducationState.course_loop, F.data == "continue")
async def course_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Курсы записаны ✅")
    await start_experience_block(callback.message, state)
    await callback.answer()


# ──────────────────────────────────────────────
# BLOCK 5 — Experience & Projects
# ──────────────────────────────────────────────

async def start_experience_block(message: Message, state: FSMContext):
    await message.answer(
        "*Блок 3 из 5 — Опыт и проекты*\n\n"
        "Нас интересует всё: организовал(а) мероприятие,\n"
        "запустил(а) что-то в Instagram, помогал(а) кому-то,\n"
        "участвовал(а) в волонтёрстве, делал(а) что-то своими руками.\n\n"
        "Не важно, большое это было или маленькое.",
        parse_mode="Markdown"
    )
    await message.answer(
        "Было ли у тебя что-то подобное — любой проект, инициатива или активность вне уроков?",
        reply_markup=kb_yes_skip()
    )
    await state.set_state(ExperienceState.filter)


@router.callback_query(ExperienceState.filter, F.data == "yes")
async def experience_yes(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Как называется или как ты бы описал(а) этот проект / активность?\n\n"
        "Например: экологическая акция, школьный подкаст, Telegram-канал о кино"
    )
    await state.set_state(ExperienceState.name)
    await callback.answer()


@router.callback_query(ExperienceState.filter, F.data == "skip")
async def experience_skip(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Опыт пропущен.")
    await start_essay_block(callback.message, state)
    await callback.answer()


@router.message(ExperienceState.name)
async def process_project_name(message: Message, state: FSMContext):
    if not (2 <= len(message.text.strip()) <= 100):
        await message.answer("Напиши от 2 до 100 символов.")
        return
    await state.update_data(current_project={"name": message.text.strip()})
    await message.answer("На что это больше всего похоже?", reply_markup=kb_project_type())
    await state.set_state(ExperienceState.type)


@router.callback_query(ExperienceState.type, F.data.startswith("type_"))
async def process_project_type(callback: CallbackQuery, state: FSMContext):
    ptype = callback.data.replace("type_", "")
    data = await state.get_data()
    project = data.get("current_project", {})
    project["type"] = ptype
    await state.update_data(current_project=project)
    await callback.message.edit_text("В каком году это было (или началось)?")
    await state.set_state(ExperienceState.year)
    await callback.answer()


@router.message(ExperienceState.year)
async def process_project_year(message: Message, state: FSMContext):
    year = validate_year(message.text)
    if year is None:
        await message.answer("Введи год от 2018 до 2026.")
        return
    data = await state.get_data()
    project = data.get("current_project", {})
    project["year"] = year
    await state.update_data(current_project=project)
    await message.answer("Какова была твоя роль?", reply_markup=kb_role())
    await state.set_state(ExperienceState.role)


@router.callback_query(ExperienceState.role, F.data.startswith("role_"))
async def process_project_role(callback: CallbackQuery, state: FSMContext):
    role = callback.data.replace("role_", "")
    data = await state.get_data()
    project = data.get("current_project", {})
    project["role"] = role
    await state.update_data(current_project=project)
    await callback.message.edit_text(
        "Сколько человек участвовало, включая тебя?\nНапиши число. Если был(а) один(а) — напиши 1."
    )
    await state.set_state(ExperienceState.team_size)
    await callback.answer()


@router.message(ExperienceState.team_size)
async def process_team_size(message: Message, state: FSMContext):
    size = validate_team_size(message.text)
    if size is None:
        await message.answer("Напиши целое число от 1 до 500.")
        return
    data = await state.get_data()
    project = data.get("current_project", {})
    project["team_size"] = size
    await state.update_data(current_project=project)
    await message.answer(
        "Опиши коротко, что именно ты делал(а) и что получилось.\n"
        "2–3 предложения, своими словами.\n\n"
        "Например: «Организовала 3 субботника, привлекла 40 волонтёров»"
    )
    await state.set_state(ExperienceState.description)


@router.message(ExperienceState.description)
async def process_project_description(message: Message, state: FSMContext):
    text = message.text.strip()
    if not (20 <= len(text) <= 500):
        await message.answer("Напиши от 20 до 500 символов.")
        return
    data = await state.get_data()
    project = data.get("current_project", {})
    project["description"] = text
    await state.update_data(current_project=project)
    await message.answer(
        "Было ли что-то, что пошло не так в этом проекте?",
        reply_markup=kb_failure()
    )
    await state.set_state(ExperienceState.failure_filter)


@router.callback_query(ExperienceState.failure_filter, F.data == "failure_yes")
async def project_failure_yes(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Что случилось и что ты сделал(а)?\nНапиши коротко — 1–2 предложения.")
    await state.set_state(ExperienceState.failure_note)
    await callback.answer()


@router.callback_query(ExperienceState.failure_filter, F.data == "failure_no")
async def project_failure_no(callback: CallbackQuery, state: FSMContext):
    await save_project(callback.from_user.id, state, failure_note=None, continued=None)
    await callback.message.edit_text("Проект записан.")
    await ask_project_loop(callback.message, state)
    await callback.answer()


@router.message(ExperienceState.failure_note)
async def process_failure_note(message: Message, state: FSMContext):
    text = message.text.strip()
    if not (10 <= len(text) <= 300):
        await message.answer("Напиши от 10 до 300 символов.")
        return
    data = await state.get_data()
    project = data.get("current_project", {})
    project["failure_note"] = text
    await state.update_data(current_project=project)
    await message.answer("Ты продолжил(а) работу после этого?", reply_markup=kb_continued())
    await state.set_state(ExperienceState.continued)


@router.callback_query(ExperienceState.continued, F.data.in_(["continued_yes", "continued_no"]))
async def process_continued(callback: CallbackQuery, state: FSMContext):
    continued = callback.data == "continued_yes"
    data = await state.get_data()
    project = data.get("current_project", {})
    await save_project(
        callback.from_user.id, state,
        failure_note=project.get("failure_note"),
        continued=continued
    )
    await callback.message.edit_text("Проект записан ✅")
    await ask_project_loop(callback.message, state)
    await callback.answer()


async def save_project(user_id: int, state: FSMContext, failure_note, continued):
    data = await state.get_data()
    project = data.get("current_project", {})
    if failure_note is not None:
        project["failure_note"] = failure_note
    if continued is not None:
        project["continued_after_failure"] = continued
    app = await get_application(user_id)
    projects = list(app.projects or [])
    projects.append(project)
    await update_application(user_id, projects=projects, funnel_stage="projects_done")


async def ask_project_loop(message: Message, state: FSMContext):
    app = await get_application(message.chat.id)
    count = len(app.projects or [])
    if count >= MAX_PROJECTS:
        await message.answer(f"Достигнут лимит проектов ({MAX_PROJECTS}).")
        await start_essay_block(message, state)
    else:
        await message.answer(
            f"Добавить ещё один проект или активность? ({count} из {MAX_PROJECTS})",
            reply_markup=kb_add_more()
        )
        await state.set_state(ExperienceState.loop)


@router.callback_query(ExperienceState.loop, F.data == "add_more")
async def project_add_more(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Как называется следующий проект или активность?"
    )
    await state.set_state(ExperienceState.name)
    await callback.answer()


@router.callback_query(ExperienceState.loop, F.data == "continue")
async def project_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Проекты записаны ✅")
    await start_essay_block(callback.message, state)
    await callback.answer()


# ──────────────────────────────────────────────
# BLOCK 6 — Essay
# ──────────────────────────────────────────────

async def start_essay_block(message: Message, state: FSMContext):
    await message.answer(
        "*Блок 4 из 5 — Эссе*\n\n"
        "Последняя текстовая часть — один вопрос.\n\n"
        "Здесь нет правильного ответа и не нужен красивый слог.\n"
        "Нам важно понять, как ты думаешь — своими словами.",
        parse_mode="Markdown"
    )
    await message.answer(
        "Вспомни один конкретный момент — не жизненную позицию,\n"
        "не «я всегда», а один день, одну ситуацию, одно решение.\n\n"
        "Что именно произошло? Что ты почувствовал(а) тогда?\n"
        "Что сделал(а) и чем это закончилось?\n\n"
        "Напиши 70–150 слов — своими словами, без подготовки.\n"
        "*Черновик лучше идеального текста.*",
        parse_mode="Markdown"
    )
    await state.set_state(EssayState.writing)


@router.message(EssayState.writing)
async def process_essay(message: Message, state: FSMContext):
    ok, wc, err = validate_essay(message.text)
    if not ok:
        await message.answer(f"❌ {err}\nПопробуй снова.")
        return

    essay_text = message.text.strip()
    await update_application(
        message.from_user.id,
        essay_text=essay_text,
        essay_word_count=wc,
        funnel_stage="essay_done"
    )

    # Run NLP analysis once, immediately after essay submission.
    # Result is stored in DB — never recomputed later.
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
        from nlp.nlp_model import analyze_essay
        nlp_result = await asyncio.get_event_loop().run_in_executor(
            None, analyze_essay, essay_text
        )
        essay_nlp = nlp_result["scores"]  # dict with model_the_way, ..., overall (0–10 scale)
        await update_application(message.from_user.id, essay_nlp=essay_nlp)
    except Exception as e:
        logger.error(f"NLP essay analysis failed for user {message.from_user.id}: {e}")
        # Do not block the candidate — NLP failure is non-fatal at collection stage.
        # The scoring pipeline will raise if essay_nlp is missing.

    await message.answer(f"✅ Эссе принято — {wc} слов. Отличная работа!")
    await start_scenarios(message, state)


# ──────────────────────────────────────────────
# BLOCK 7 — Scenarios (full branching 25-question tree)
# ──────────────────────────────────────────────

def get_progress_bar(seconds_left: int, total: int) -> str:
    filled = round((seconds_left / total) * 10)
    return "█" * filled + "░" * (10 - filled)


async def start_scenarios(message: Message, state: FSMContext):
    await message.answer(
        "*Блок 5 из 5 — Сценарии*\n\n"
        "Осталось 5 ситуаций — в каждой два шага.\n\n"
        f"У тебя будет {SCENARIO_TIMER_SECONDS} секунд на каждый ответ.\n"
        "Нет правильных или неправильных вариантов —\n"
        "нас интересует, как именно ты думаешь.",
        reply_markup=kb_go(),
        parse_mode="Markdown"
    )
    await state.set_state(ScenarioState.intro)
    await state.update_data(
        scenario_idx=0,
        scenario_phase="entry",
        scenario_entry_choice=None,
        choice_path=[],
        timer_violations=0
    )


@router.callback_query(ScenarioState.intro, F.data == "scenario_go")
async def scenario_go(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.message.edit_text("Начинаем! ⏱")
    await send_scenario_question(bot, callback.from_user.id, state)
    await callback.answer()


async def send_scenario_question(bot: Bot, user_id: int, state: FSMContext, edit_message_id: int = None):
    """
    Принимает edit_message_id. Если он есть — редактирует старое сообщение.
    Если нет — отправляет новое.
    """
    data = await state.get_data()
    idx = data.get("scenario_idx", 0)
    phase = data.get("scenario_phase", "entry")
    sc_id = SCENARIO_ORDER[idx]

    q_text = get_question_text(sc_id, phase)
    markup = kb_scenario(sc_id, phase)

    sc_num = idx + 1
    phase_label = "Шаг 1 из 2" if phase == "entry" else "Шаг 2 из 2"
    header = f"*Сценарий {sc_num} из 5 — {phase_label}*\n\n"

    full_text = (
        f"⏱ ██████████ {SCENARIO_TIMER_SECONDS} сек\n\n"
        f"{header}{q_text}"
    )

    if edit_message_id:
        try:
            sent = await bot.edit_message_text(
                chat_id=user_id,
                message_id=edit_message_id,
                text=full_text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except TelegramBadRequest:
            sent = await bot.send_message(user_id, full_text, reply_markup=markup, parse_mode="Markdown")
    else:
        sent = await bot.send_message(user_id, full_text, reply_markup=markup, parse_mode="Markdown")

    await state.set_state(ScenarioState.answering)
    current_q_key = f"{idx}_{phase}"

    asyncio.create_task(
        scenario_timer(
            bot=bot,
            user_id=user_id,
            msg_id=sent.message_id,
            state=state,
            header=header,
            question_text=q_text,
            reply_markup=markup,
            q_key=current_q_key
        )
    )

async def scenario_timer(
    bot: Bot,
    user_id: int,
    msg_id: int,
    state: FSMContext,
    header: str,
    question_text: str,
    reply_markup: InlineKeyboardMarkup,
    q_key: str
):
    seconds = SCENARIO_TIMER_SECONDS

    while seconds > 0:
        await asyncio.sleep(1)

        data = await state.get_data()
        current_state = await state.get_state()
        active_q_key = f"{data.get('scenario_idx')}_{data.get('scenario_phase')}"

        if current_state != ScenarioState.answering.state or active_q_key != q_key:
            return  # Выходим, если пользователь уже ответил или перешел к след. вопросу

        seconds -= 1

        if seconds % 2 == 0 or seconds <= 5:
            bar = get_progress_bar(seconds, SCENARIO_TIMER_SECONDS)
            try:
                await bot.edit_message_text(
                    chat_id=user_id,
                    message_id=msg_id,
                    text=f"⏱ {bar} {seconds} сек\n\n{header}{question_text}",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            except TelegramBadRequest:
                pass

    # Время вышло
    current_state = await state.get_state()
    data = await state.get_data()
    active_q_key = f"{data.get('scenario_idx')}_{data.get('scenario_phase')}"
    
    if current_state == ScenarioState.answering.state and active_q_key == q_key:
        violations = data.get("timer_violations", 0) + 1
        await state.update_data(timer_violations=violations)

        try:
            await bot.edit_message_reply_markup(chat_id=user_id, message_id=msg_id, reply_markup=None)
        except TelegramBadRequest:
            pass

        await bot.send_message(user_id, "⏰ Время вышло! Переходим дальше.")
        await advance_scenario(bot, user_id, state, chosen_letter=None, msg_id=msg_id)

@router.callback_query(ScenarioState.answering, F.data.startswith("ans_"))
async def scenario_answer(callback: CallbackQuery, state: FSMContext, bot: Bot):
    parts = callback.data.split("_")
    chosen_letter = parts[-1] 

    await advance_scenario(bot, callback.from_user.id, state, chosen_letter=chosen_letter, msg_id=callback.message.message_id)
    await callback.answer()

async def advance_scenario(bot: Bot, user_id: int, state: FSMContext, chosen_letter: str | None, msg_id: int):
    data = await state.get_data()
    idx = data.get("scenario_idx", 0)
    phase = data.get("scenario_phase", "entry")
    choice_path = data.get("choice_path", [])



    if chosen_letter is None:
        choice_path.append("T")

        if phase == "entry":
            choice_path.append("T")


        next_idx = idx + 1
        await state.update_data(choice_path=choice_path)

        if next_idx < len(SCENARIO_ORDER):
            await state.update_data(
                scenario_idx=next_idx,
                scenario_phase="entry",
                scenario_entry_choice=None
            )
            await send_scenario_question(bot, user_id, state, edit_message_id=msg_id)
        else:
            try:
                await bot.edit_message_reply_markup(chat_id=user_id, message_id=msg_id, reply_markup=None)
            except:
                pass
            await finish_scenarios(bot, user_id, state)
        return

    choice_path.append(chosen_letter)

    if phase == "entry":
        await state.update_data(
            choice_path=choice_path,
            scenario_phase=chosen_letter,
            scenario_entry_choice=chosen_letter
        )
        await send_scenario_question(bot, user_id, state, edit_message_id=msg_id)

    else:
        next_idx = idx + 1
        await state.update_data(choice_path=choice_path)

        if next_idx < len(SCENARIO_ORDER):
            await state.update_data(
                scenario_idx=next_idx,
                scenario_phase="entry",
                scenario_entry_choice=None
            )
            await send_scenario_question(bot, user_id, state, edit_message_id=msg_id)
        else:
            try:
                await bot.edit_message_reply_markup(chat_id=user_id, message_id=msg_id, reply_markup=None)
            except:
                pass
            await finish_scenarios(bot, user_id, state)


async def finish_scenarios(bot: Bot, user_id: int, state: FSMContext):
    data = await state.get_data()
    choice_path = data.get("choice_path", [])
    violations = data.get("timer_violations", 0)

    # fingerprint = compute_fingerprint(choice_path)   OLD FINGERPRINT FROM HELPER
    # reliable = violations <= 2    OLD FINGERPRINT FROM HELPER

    timer_compliant = [ch != "T" for ch in choice_path]

    fp_result = compute_fingerprint(choice_path, timer_compliant=timer_compliant)
    # Override reliability with the actual event-based violation count (violations
    # counts timeout events, not individual T-entries; 2 entry timeouts → 4 T-entries
    # but only 2 events — we allow up to 3 events before marking unreliable).
    if fp_result["fingerprint_reliable"] is not None:
        fp_result["fingerprint_reliable"] = violations <= 3

    await update_application(
        user_id,
        scenario_choices={"choices": choice_path},
        # fingerprint_display=fingerprint,  OLD FINGERPRINT FROM HELPER
        # fingerprint_reliable=reliable,    OLD FINGERPRINT FROM HELPER
        fingerprint_display=fp_result["fingerprint_display"],
        fingerprint_reliable=fp_result["fingerprint_reliable"],
        timer_violations=violations,
        funnel_stage="scenarios_done"
    )

    text = "✅ Сценарии завершены!\n\n"
    if not fp_result["fingerprint_reliable"]:
        text += "⚠️ Некоторые ответы не засчитаны из-за таймера.\n\n"
    text += "Последний шаг — можешь прикрепить материалы."

    await bot.send_message(user_id, text)
    await ask_file_upload(bot, user_id, state)


# ──────────────────────────────────────────────
# BLOCK 8 — File Upload
# ──────────────────────────────────────────────

async def ask_file_upload(bot: Bot, user_id: int, state: FSMContext):
    await bot.send_message(
        user_id,
        "📎 *Дополнительные материалы*\n\n"
        "Хочешь прикрепить файлы к заявке?\n"
        "Это могут быть: сертификаты, портфолио, грамоты, скриншоты проектов.\n\n"
        "Поддерживаются: PDF, изображения, документы (до 20 МБ каждый).",
        reply_markup=kb_upload_file(),
        parse_mode="Markdown"
    )
    await state.set_state(FileUploadState.waiting)


@router.callback_query(FileUploadState.waiting, F.data == "upload_file")
async def upload_file_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Отправь файл(ы) одним сообщением или по одному.\n"
        "Когда закончишь — нажми /done или напиши «готово»."
    )
    await callback.answer()


@router.callback_query(FileUploadState.waiting, F.data == "skip_upload")
async def skip_upload(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Файлы пропущены.")
    await finalize_application(callback.message, state, callback.from_user.id)
    await callback.answer()


@router.message(FileUploadState.waiting, F.document | F.photo | F.video)
async def handle_file_upload(message: Message, state: FSMContext):
    file_info = {}
    if message.document:
        file_info = {
            "type": "document",
            "file_id": message.document.file_id,
            "file_name": message.document.file_name,
            "mime_type": message.document.mime_type,
            "file_size": message.document.file_size,
        }
    elif message.photo:
        photo = message.photo[-1]
        file_info = {
            "type": "photo",
            "file_id": photo.file_id,
            "file_size": photo.file_size,
        }
    elif message.video:
        file_info = {
            "type": "video",
            "file_id": message.video.file_id,
            "file_name": message.video.file_name,
            "file_size": message.video.file_size,
        }

    app = await get_application(message.from_user.id)
    files = list(app.uploaded_files or [])
    files.append(file_info)
    await update_application(message.from_user.id, uploaded_files=files)
    await message.answer(f"✅ Файл #{len(files)} получен. Отправь ещё или напиши /done")


@router.message(FileUploadState.waiting, F.text.lower().in_(["готово", "done", "/done"]))
@router.message(Command("done"))
async def files_done(message: Message, state: FSMContext):
    current = await state.get_state()
    if current == FileUploadState.waiting.state:
        await finalize_application(message, state, message.from_user.id)


# ──────────────────────────────────────────────
# BLOCK 9 — Finalize
# ──────────────────────────────────────────────

async def finalize_application(message: Message, state: FSMContext, user_id: int):
    await update_application(user_id, funnel_stage="submitted")
    app = await get_application(user_id)
    if app:
        try:
            path = save_to_json(app)
            logger.info(f"JSON saved for user {user_id}: {path}")
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")

    summary = build_summary(app)
    await message.answer(
        "🎉 *Заявка успешно отправлена!*\n\n"
        "Мы изучим её и свяжемся с тобой в течение 2–3 дней.\n\n"
        "Удачи! Ниже — резюме того, что ты заполнил(а):\n\n" + summary,
        parse_mode="Markdown"
    )
    await state.clear()


# ──────────────────────────────────────────────
# Admin: /status
# ──────────────────────────────────────────────

@router.message(Command("status"))
async def cmd_status(message: Message):
    app = await get_application(message.from_user.id)
    if not app:
        await message.answer("Заявка не найдена. Напиши /start")
        return
    await message.answer(
        f"Статус твоей заявки: *{app.funnel_stage}*",
        parse_mode="Markdown"
    )