from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
def kb_start():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Начать 🚀", callback_data="start_app"),
            InlineKeyboardButton(text="Что такое InVision U?", callback_data="about"),
        ]
    ])
def kb_about_back():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Понятно, начинаем 🚀", callback_data="start_app")]
    ])
def kb_consent():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, согласен(а)", callback_data="consent_yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="consent_no"),
        ]
    ])
def kb_yes_skip():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="yes"),
            InlineKeyboardButton(text="➡️ Нет, пропустить", callback_data="skip"),
        ]
    ])
def kb_olympiad_level():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌍 Международный", callback_data="level_international")],
        [InlineKeyboardButton(text="🇰🇿 Республиканский", callback_data="level_republican")],
        [InlineKeyboardButton(text="🏙️ Областной / городской", callback_data="level_regional")],
        [InlineKeyboardButton(text="🏫 Школьный", callback_data="level_school")],
    ])
def kb_prize():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🥇 Да, есть призовое место", callback_data="prize_yes"),
            InlineKeyboardButton(text="Нет, участие", callback_data="prize_no"),
        ]
    ])
def kb_add_more():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="add_more"),
            InlineKeyboardButton(text="➡️ Продолжить", callback_data="continue"),
        ]
    ])
def kb_completed():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, прошёл(а) полностью", callback_data="completed_yes"),
            InlineKeyboardButton(text="⏸️ Нет, не до конца", callback_data="completed_no"),
        ]
    ])
def kb_project_type():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💻 Технический (код, приложение, сайт)", callback_data="type_technical")],
        [InlineKeyboardButton(text="🌱 Социальный / волонтёрский", callback_data="type_social")],
        [InlineKeyboardButton(text="🎨 Творческий (медиа, музыка, арт)", callback_data="type_creative")],
        [InlineKeyboardButton(text="💼 Бизнес / предпринимательство", callback_data="type_business")],
        [InlineKeyboardButton(text="📚 Образовательный (кружок, курс, команда)", callback_data="type_educational")],
        [InlineKeyboardButton(text="🔀 Другое", callback_data="type_other")],
    ])
def kb_role():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Я основал(а) / запустил(а) сам(а)", callback_data="role_founder")],
        [InlineKeyboardButton(text="🤝 Я был(а) сооснователем", callback_data="role_co_founder")],
        [InlineKeyboardButton(text="⭐ Ключевой участник", callback_data="role_key_member")],
        [InlineKeyboardButton(text="👥 Рядовой участник", callback_data="role_participant")],
    ])
def kb_failure():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, были трудности", callback_data="failure_yes"),
            InlineKeyboardButton(text="➡️ Нет / не помню", callback_data="failure_no"),
        ]
    ])
def kb_continued():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, продолжил(а)", callback_data="continued_yes"),
            InlineKeyboardButton(text="➡️ Нет / завершился", callback_data="continued_no"),
        ]
    ])
def kb_scenario_step1():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A — Беру всё на себя", callback_data="sc1_A")],
        [InlineKeyboardButton(text="B — Собираю команду и распределяю задачи", callback_data="sc1_B")],
        [InlineKeyboardButton(text="C — Ищу замену организатору", callback_data="sc1_C")],
        [InlineKeyboardButton(text="D — Сообщаю куратору / старшему", callback_data="sc1_D")],
    ])
def kb_scenario_step2():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A — Оставляю — каждый заслуживает шанс", callback_data="sc2_A")],
        [InlineKeyboardButton(text="B — Заменяю — результат команды важнее", callback_data="sc2_B")],
        [InlineKeyboardButton(text="C — Сначала поговорю напрямую", callback_data="sc2_C")],
        [InlineKeyboardButton(text="D — Тихо перераспределяю задачи", callback_data="sc2_D")],
    ])
def kb_scenario_step3():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A — Действую по плану, риск не нужен", callback_data="sc3_A")],
        [InlineKeyboardButton(text="B — Предлагаю новый подход, объясняю команде", callback_data="sc3_B")],
        [InlineKeyboardButton(text="C — Тестирую идею на малой группе", callback_data="sc3_C")],
        [InlineKeyboardButton(text="D — Жду финала, потом предлагаю изменения", callback_data="sc3_D")],
    ])
def kb_scenario_step4():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="A — Решаю сам(а), не трачу время команды", callback_data="sc4_A")],
        [InlineKeyboardButton(text="B — Прошу команду предложить варианты", callback_data="sc4_B")],
        [InlineKeyboardButton(text="C — Нахожу эксперта и спрашиваю его", callback_data="sc4_C")],
        [InlineKeyboardButton(text="D — Анализирую данные, потом решаю", callback_data="sc4_D")],
    ])
def kb_go():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Поехали ▶️", callback_data="scenario_go")]
    ])
def kb_no_ielts():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Если нет — нажми сюда", callback_data="no_ielts")]
    ])
def kb_no_ent():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Если нет — нажми сюда", callback_data="no_ent")]
    ])
def kb_skip_cert():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_cert")]
    ])
def kb_upload_file():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📎 Прикрепить файл", callback_data="upload_file")],
        [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_upload")],
    ])
def kb_done():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Готово", callback_data="finish")]
    ])
kb_school = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Общеобразовательная", callback_data="school:general")],
    [InlineKeyboardButton(text="Лицей",               callback_data="school:lyceum")],
    [InlineKeyboardButton(text="Гимназия",            callback_data="school:gymnasium")],
    [InlineKeyboardButton(text="Специализированная",  callback_data="school:specialized")],
    [InlineKeyboardButton(text="Домашнее обучение",   callback_data="school:homeschool")],
    [InlineKeyboardButton(text="Колледж",             callback_data="school:college")],
    [InlineKeyboardButton(text="Другое",              callback_data="school:other")],
])
