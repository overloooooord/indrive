import bcrypt
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.conf import settings
import json
logger = logging.getLogger('candidates')

@ensure_csrf_cookie
def index(request):
    return render(request, 'frontend/index.html')

@ensure_csrf_cookie
def register(request):
    return render(request, 'frontend/register.html')
def candidate_detail(request, pk):
    return render(request, 'frontend/candidate_detail.html', {'candidate_id': pk})
def panel_view(request):
    if not request.session.get('panel_auth'):
        return redirect('panel-login-page')
    return render(request, 'frontend/admin_panel.html')
def panel_login_page(request):
    if request.session.get('panel_auth'):
        return redirect('panel')
    if request.session.get('teacher_auth'):
        return redirect('teacher-panel')
    return render(request, 'frontend/login.html')
@csrf_exempt
def panel_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    expected_user = getattr(settings, 'PANEL_USERNAME', 'admin')
    panel_password = getattr(settings, 'PANEL_PASSWORD', '')

    # Fallback to plain password if env var is missing or empty
    if not panel_password:
        panel_password = 'admin'

    # ── Admin check ───────────────────────────────────────────────
    if username == expected_user and password == panel_password:
        request.session['panel_auth'] = True
        logger.info(f"Вход в админ-панель: {username}")
        return JsonResponse({'success': True, 'redirect': '/panel/'})

    # ── Teacher check ─────────────────────────────────────────────
    teachers = getattr(settings, 'TEACHERS', {})

    if not teachers:
        teachers = {
            'teacher': {
                'password': 'teacher',
                'name': 'Test Teacher (Fallback)'
            }
        }

    # DEBUG: выводим что загружено из TEACHERS_JSON
    logger.warning(f"[LOGIN DEBUG] username='{username}' | TEACHERS keys={list(teachers.keys())} | username_in_teachers={username in teachers}")

    if username in teachers:
        teacher = teachers[username]
        # Поддерживаем оба ключа: 'password' и 'password_hash'
        teacher_password = teacher.get('password', '') or teacher.get('password_hash', '')
        passwords_match = teacher_password and password == teacher_password
        logger.warning(f"[LOGIN DEBUG] teacher found | has_password_key={'password' in teacher} | has_password_hash_key={'password_hash' in teacher} | passwords_match={passwords_match}")
        if passwords_match:
            request.session['teacher_auth'] = username
            request.session['teacher_name'] = teacher.get('name', username)
            logger.info(f"Вход в кабинет учителя: {username} ({teacher.get('name', '')})")
            return JsonResponse({'success': True, 'redirect': '/teacher/'})
        logger.warning(f"[LOGIN DEBUG] teacher password mismatch for username={username}")

    logger.warning(f"Неудачная попытка входа: username={username} | teachers_loaded={len(teachers)}")
    return JsonResponse(
        {'success': False, 'error': 'Неверный логин или пароль'},
        status=401,
    )
def panel_logout(request):
    request.session.pop('panel_auth', None)
    logger.info("Выход из админ-панели")
    return redirect('panel-login-page')
def teacher_view(request):
    if not request.session.get('teacher_auth'):
        return redirect('panel-login-page')
    teacher_login = request.session['teacher_auth']
    teacher_name = request.session.get('teacher_name', teacher_login)
    return render(request, 'frontend/teacher_panel.html', {
        'teacher_login': teacher_login,
        'teacher_name': teacher_name,
    })
def teacher_logout(request):
    teacher = request.session.pop('teacher_auth', None)
    request.session.pop('teacher_name', None)
    logger.info(f"Выход из кабинета учителя: {teacher}")
    return redirect('panel-login-page')
