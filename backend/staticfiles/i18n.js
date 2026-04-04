/**
 * i18n.js — Мультиязычность (RU / KZ / EN)
 * ==========================================
 *
 * КАК ЭТО РАБОТАЕТ (для начинающих):
 *
 *   1. В HTML у текстовых элементов стоит атрибут data-i18n="ключ"
 *      Например: <h2 data-i18n="reg_title">Заявка</h2>
 *
 *   2. В объекте TRANSLATIONS хранятся переводы для каждого языка:
 *      { ru: { reg_title: "Заявка" }, kz: { reg_title: "Өтінім" }, en: { reg_title: "Application" } }
 *
 *   3. Функция setLanguage('kz') находит ВСЕ элементы с data-i18n
 *      и заменяет их текст на перевод из нужного языка.
 *
 *   4. Выбранный язык сохраняется в localStorage → при перезагрузке
 *      страницы язык не сбрасывается.
 */

'use strict';

// ─── Словарь переводов ────────────────────────────────────────────────────────
const TRANSLATIONS = {

  // ═══════════════════════════════════════════════════
  // РУССКИЙ
  // ═══════════════════════════════════════════════════
  ru: {
    // Header
    apply_btn:      'Подать заявку',

    // Landing / Hero
    badge:          '✨ Программа отбора 2026',
    hero_line1:     'Поступи в',
    hero_sub:       'Заполни анкету, пройди MBTI тест и языковой тест. Все данные защищены и отправляются в нашу систему.',
    cta_note:       'Бесплатно · ~15 минут · Данные защищены',
    steps:          'Шага',
    test:           'Тест',
    safe:           'Безопасно',

    // Registration form
    reg_title:      'Заявка',
    reg_sub:        'Заполни все поля для подачи заявки',
    
    // Landing specifics
    land_founder_tag: 'Основатель',
    land_founder_title: 'inVision U основан и спонсируется Арсеном Томским',
    land_founder_p1: 'Основатель и CEO inDrive — глобальной компании, борющейся с неравным распределением возможностей и знаний.',
    land_founder_p2: 'В основе inVision U лежит инновационный командный подход к воспитанию лидеров, способных изменить мир к лучшему.',
    land_grant: 'Грантовое обучение. Проживание, питание и стипендия для тех, кто в этом нуждается.',
    land_partner: 'Партнёрство с Satbayev University — диплом государственного образца',
    land_mission_tag: 'Миссия',
    land_mission_title: 'Пять составляющих миссии',
    land_m1_t: 'Доступность',
    land_m1_d: 'Грантовое обучение для всех. Полностью финансируемый Foundation Year для студентов из малообеспеченных регионов.',
    land_m2_t: 'Думать по-другому',
    land_m2_d: 'Программа строится на практических задачах и командных проектах, сочетая личное развитие с совместным обучением.',
    land_m3_t: 'Применять знания',
    land_m3_d: 'Пять взаимосвязанных программ. Выпускной командный проект — решение реальной проблемы общества.',
    land_m4_t: 'Сохранять таланты',
    land_m4_d: 'Большинство студентов и преподавателей из региона обучения. Поддержка в постдипломных проектах.',
    land_m5_t: 'Наука + обучение',
    land_m5_d: 'Преподаватели и студенты исследуют местные проблемы, создавая решения, влияющие на политику.',
    land_map_p1: 'Использование самых передовых методов обучения, включая проектное обучение, дизайн-мышление и AR/VR-технологии.',
    land_map_p2: 'Выпускники останутся в своих странах и регионах, чтобы внести вклад в их развитие.',
    land_future: 'Планы на будущее',
    land_campuses: 'кампусов по миру',
    land_students: 'студентов',
    land_cta_title: 'Готов изменить мир?',
    land_cta_sub: 'Забудь о долгах после университета. Фокусируйся на росте, лидерстве и реальных проектах.',
    label_name:     'Имя и фамилия *',
    label_city:     'Город *',
    label_region:   'Регион',
    label_langs:    'Знание языков *',
    label_tg:       'Telegram username *',
    label_hobbies:  'Хобби',
    label_sport:    'Спорт',
    choose:         '— выберите —',
    next_btn:       'Далее — MBTI тест →',
    ph_name:        'Иван Иванов',
    ph_region:      'Заполнится автоматически',
    ph_tg:          '@username',
    ph_hobbies:     'Чтение, музыка...',
    ph_sport:       'Плавание, бег...',

    // Validation errors
    err_fill_all:   'Пожалуйста, заполните все обязательные поля',
    err_select_lang:'Выберите хотя бы один язык',
    err_tg_format:  'Введите корректный Telegram username',

    // MBTI test
    mbti_title:     'Психометрический тест',
    back:           '← Назад',
    next_q:         'Далее →',
    finish_mbti:    'Завершить тест →',
    mbti_pick:      'Выберите один из вариантов',

    // Language test
    lang_title:     'Языковой тест',
    violations:     'Выходы из вкладки: 0',
    violation_warn: '⚠ Внимание! Не покидайте вкладку во время теста. Следующий выход приведёт к блокировке.',
    violation_block:'Тест заблокирован из-за повторного выхода из вкладки. Результаты отправлены автоматически.',
    finish_lang:    'Завершить тест →',
    time_up:        'Время вышло! Результаты отправлены автоматически.',

    // Submission
    sending:        'Отправляем...',
    send_error:     'Ошибка при отправке. Попробуйте ещё раз.',

    // Success
    success_title:  'Заявка отправлена!',
    success_sub:    'Все данные сохранены. Спасибо за заявку!',
    tg_redirect:    'Перейдите в Telegram, чтобы отслеживать статус вашей заявки:',
    go_home:        'На главную',

    // Login
    login_btn:      'Войти',
    login_title:    'Вход в панель',
    login_sub:      'Авторизация для администраторов',
    login_user:     'Логин',
    login_pass:     'Пароль',
    login_ok:       'Успешный вход!',
    login_fail:     'Неверный логин или пароль',
    ph_login:       'Введите логин',
  },

  // ═══════════════════════════════════════════════════
  // ҚАЗАҚША
  // ═══════════════════════════════════════════════════
  kz: {
    apply_btn:      'Өтінім беру',

    badge:          '✨ Іріктеу бағдарламасы 2026',
    hero_line1:     'Түсу',
    hero_sub:       'Анкетаны толтырыңыз, MBTI тестін және тіл тестін тапсырыңыз. Барлық деректер қорғалған.',
    cta_note:       'Тегін · ~15 минут · Деректер қорғалған',
    steps:          'Қадам',
    test:           'Тест',
    safe:           'Қауіпсіз',

    reg_title:      'Өтінім',
    reg_sub:        'Өтінім беру үшін барлық өрістерді толтырыңыз',
    
    // Landing specifics
    land_founder_tag: 'Негізін қалаушы',
    land_founder_title: 'inVision U негізін Арсен Томский қалады',
    land_founder_p1: 'inDrive негізін қалаушы және CEO — мүмкіндіктер теңсіздігімен күресетін жаһандық компания.',
    land_founder_p2: 'inVision U негізінде әлемді өзгерте алатын көшбасшыларды тәрбиелеу тәсілі жатыр.',
    land_grant: 'Гранттық оқыту. Мұқтаж жандарға тұру, тамақтану және стипендия.',
    land_partner: 'Satbayev University-мен серіктестік — мемлекеттік үлгідегі диплом',
    land_mission_tag: 'Миссия',
    land_mission_title: 'Миссияның бес құрамдас бөлігі',
    land_m1_t: 'Қолжетімділік',
    land_m1_d: 'Барлығына гранттық оқыту. Foundation Year толығымен қаржыландырылады.',
    land_m2_t: 'Басқаша ойлау',
    land_m2_d: 'Бағдарлама тәжірибелік тапсырмалар мен командалық жобаларға негізделген.',
    land_m3_t: 'Білімді қолдану',
    land_m3_d: 'Бес бағдарлама. Бітіруші жоба — қоғам мәселесін шешу.',
    land_m4_t: 'Таланттарды сақтау',
    land_m4_d: 'Студенттер мен оқытушылардың көпшілігі оқу аймағынан қалады.',
    land_m5_t: 'Ғылым + оқыту',
    land_m5_d: 'Жергілікті мәселелерді зерттеп, саясатқа әсер ететін шешімдер.',
    land_map_p1: 'Жобалық оқыту, дизайндық ойлау, AR/VR технологияларын қолдану.',
    land_map_p2: 'Түлектер өз елдерінің дамуына үлес қосу үшін сол жерде қалады.',
    land_future: 'Болашақ жоспарлар',
    land_campuses: 'әлем бойынша кампус',
    land_students: 'студенттер',
    land_cta_title: 'Әлемді өзгертуге дайынсыз ба?',
    land_cta_sub: 'Қарыздарды ұмытыңыз. Өсу мен көшбасшылыққа назар аударыңыз.',
    label_name:     'Аты-жөні *',
    label_city:     'Қала *',
    label_region:   'Аймақ',
    label_langs:    'Тіл білімі *',
    label_tg:       'Telegram username *',
    label_hobbies:  'Хобби',
    label_sport:    'Спорт',
    choose:         '— таңдаңыз —',
    next_btn:       'Келесі — MBTI тест →',
    ph_name:        'Иван Иванов',
    ph_region:      'Автоматты түрде толтырылады',
    ph_tg:          '@username',
    ph_hobbies:     'Оқу, музыка...',
    ph_sport:       'Жүзу, жүгіру...',

    err_fill_all:   'Барлық міндетті өрістерді толтырыңыз',
    err_select_lang:'Кем дегенде бір тілді таңдаңыз',
    err_tg_format:  'Дұрыс Telegram username енгізіңіз',

    mbti_title:     'Психометриялық тест',
    back:           '← Артқа',
    next_q:         'Келесі →',
    finish_mbti:    'Тестті аяқтау →',
    mbti_pick:      'Нұсқалардың бірін таңдаңыз',

    lang_title:     'Тіл тесті',
    violations:     'Қойындыдан шығу: 0',
    violation_warn: '⚠ Назар аударыңыз! Тест кезінде қойындыдан шықпаңыз. Келесі шығу блоктауға әкеледі.',
    violation_block:'Қойындыдан қайта шыққандықтан тест бұғатталды. Нәтижелер автоматты түрде жіберілді.',
    finish_lang:    'Тестті аяқтау →',
    time_up:        'Уақыт бітті! Нәтижелер автоматты түрде жіберілді.',

    sending:        'Жіберілуде...',
    send_error:     'Жіберу қатесі. Қайта көріңіз.',

    success_title:  'Өтінім жіберілді!',
    success_sub:    'Барлық деректер сақталды. Өтінім үшін рахмет!',
    tg_redirect:    'Өтінім мәртебесін бақылау үшін Telegram-ға өтіңіз:',
    go_home:        'Басты бетке',

    login_btn:      'Кіру',
    login_title:    'Панельге кіру',
    login_sub:      'Әкімшілер үшін авторизация',
    login_user:     'Логин',
    login_pass:     'Құпия сөз',
    login_ok:       'Сәтті кіру!',
    login_fail:     'Логин немесе құпия сөз қате',
    ph_login:       'Логинді енгізіңіз',
  },

  // ═══════════════════════════════════════════════════
  // ENGLISH
  // ═══════════════════════════════════════════════════
  en: {
    apply_btn:      'Apply Now',

    badge:          '✨ Selection Program 2026',
    hero_line1:     'Join',
    hero_sub:       'Fill out the application, take the MBTI test and language test. All data is protected and sent to our system.',
    cta_note:       'Free · ~15 min · Data protected',
    steps:          'Steps',
    test:           'Test',
    safe:           'Secure',

    reg_title:      'Application',
    reg_sub:        'Fill in all fields to submit your application',
    
    // Landing specifics
    land_founder_tag: 'Founder',
    land_founder_title: 'inVision U is founded and sponsored by Arsen Tomsky',
    land_founder_p1: 'Founder and CEO of inDrive — a global company fighting the unequal distribution of opportunity and knowledge.',
    land_founder_p2: 'At the core of inVision U lies an innovative team-based approach to educating leaders who can bring positive change.',
    land_grant: '100% Scholarship. Support with accommodation and meals for those in need.',
    land_partner: 'Partnership with Satbayev University — state-recognized diploma',
    land_mission_tag: 'Mission',
    land_mission_title: 'Five Pillars of Our Mission',
    land_m1_t: 'Accessibility',
    land_m1_d: 'Fully grant funded. A fully funded Foundation Year for students from low-income regions.',
    land_m2_t: 'Think Differently',
    land_m2_d: 'Practical tasks and team projects, combining personal development with collaborative learning.',
    land_m3_t: 'Apply Knowledge',
    land_m3_d: 'Five interconnected programs. The final team project solves a real social problem.',
    land_m4_t: 'Retain Talent',
    land_m4_d: 'The majority of students and teachers are from the region. Support for postgraduate projects.',
    land_m5_t: 'Science + Learning',
    land_m5_d: 'Researching local issues to create policy-influencing solutions.',
    land_map_p1: 'Using advanced teaching methods: project learning, design thinking, AR/VR technologies.',
    land_map_p2: 'Graduates will remain in their regions to contribute to local development.',
    land_future: 'Future plans',
    land_campuses: 'campuses worldwide',
    land_students: 'students',
    land_cta_title: 'Ready to change the world?',
    land_cta_sub: 'Forget post-college debt. Focus on your growth, leadership, and real projects.',
    label_name:     'Full name *',
    label_city:     'City *',
    label_region:   'Region',
    label_langs:    'Languages *',
    label_tg:       'Telegram username *',
    label_hobbies:  'Hobbies',
    label_sport:    'Sport',
    choose:         '— select —',
    next_btn:       'Next — MBTI test →',
    ph_name:        'John Smith',
    ph_region:      'Auto-filled',
    ph_tg:          '@username',
    ph_hobbies:     'Reading, music...',
    ph_sport:       'Swimming, running...',

    err_fill_all:   'Please fill in all required fields',
    err_select_lang:'Please select at least one language',
    err_tg_format:  'Please enter a valid Telegram username',

    mbti_title:     'Psychometric Test',
    back:           '← Back',
    next_q:         'Next →',
    finish_mbti:    'Finish test →',
    mbti_pick:      'Select one option',

    lang_title:     'Language Test',
    violations:     'Tab switches: 0',
    violation_warn: '⚠ Warning! Do not leave the tab during the test. Next exit will result in a block.',
    violation_block:'Test blocked due to repeated tab exit. Results submitted automatically.',
    finish_lang:    'Finish test →',
    time_up:        'Time is up! Results submitted automatically.',

    sending:        'Sending...',
    send_error:     'Submission error. Please try again.',

    success_title:  'Application sent!',
    success_sub:    'All data has been saved. Thank you for applying!',
    tg_redirect:    'Go to Telegram to track your application status:',
    go_home:        'Home',

    login_btn:      'Sign In',
    login_title:    'Admin Panel',
    login_sub:      'Authentication for administrators',
    login_user:     'Username',
    login_pass:     'Password',
    login_ok:       'Login successful!',
    login_fail:     'Invalid username or password',
    ph_login:       'Enter username',
  },
};


// ─── Текущий язык ─────────────────────────────────────────────────────────────
let currentLang = localStorage.getItem('lang') || 'ru';


// ─── Получить перевод по ключу ────────────────────────────────────────────────
function t(key) {
  const dict = TRANSLATIONS[currentLang] || TRANSLATIONS['ru'];
  return dict[key] || TRANSLATIONS['ru'][key] || key;
}


// ─── Применить язык ко всей странице ──────────────────────────────────────────
function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('lang', lang);

  // 1. Обновить все элементы с data-i18n
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const translation = t(key);
    if (translation) {
      el.textContent = translation;
    }
  });

  // 2. Обновить placeholder'ы
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.getAttribute('data-i18n-ph');
    const translation = t(key);
    if (translation) {
      el.placeholder = translation;
    }
  });

  // 3. Обновить кнопки языков в header
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  // 4. Обновить title страницы
  const titles = { ru: 'inVision U — Подать заявку', kz: 'inVision U — Өтінім беру', en: 'inVision U — Apply Now' };
  document.title = titles[lang] || titles['ru'];

  // 5. Оповестить другие модули о смене языка
  window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
}


// ─── Инициализация ────────────────────────────────────────────────────────────
function initI18n() {
  // Применить сохранённый язык
  setLanguage(currentLang);

  // Слушаем клики на кнопки языков
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      setLanguage(btn.dataset.lang);
    });
  });
}

// Запускаем при загрузке DOM
document.addEventListener('DOMContentLoaded', initI18n);
