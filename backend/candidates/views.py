
import logging
import bcrypt

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.conf import settings

from .models import (
    Candidate, ScoringResult,
    Application, BotApplication,
    TeacherNomination,
)
from .serializers import (
    CandidateListSerializer,
    CandidateDetailSerializer,
    CandidateRegisterSerializer,
    ApplicationSerializer,
    ApplicationListSerializer,
    AdminLoginSerializer,
)
from .ml_service import score_candidate, rank_candidates
from .telegram_service import notify_new_application
from .kz_regions import (
    get_all_cities, get_regions_for_city, get_all_regions,
    LANGUAGES_CHOICES,
)


# Логгеры
logger = logging.getLogger('candidates')
app_logger = logging.getLogger('candidates.applications')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ЗАЯВКИ — CRUD
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['GET', 'POST'])
def application_list_create(request):
    """
    GET  /api/applications/ — список всех заявок (с фильтрами и пагинацией)
    POST /api/applications/ — создать новую заявку

    Фильтры (query params):
      ?city=Алматы — по городу
      ?language=Казахский — по языку
      ?status=new — по статусу
      ?search=Иванов — поиск по имени
    """
    if request.method == 'POST':
        serializer = ApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        app_logger.info(
            f"Новая заявка #{application.pk}: {application.name} "
            f"из {application.city}, GPA: {application.gpa}, "
            f"олимпиад: {len(application.olympiads or [])}, "
            f"проектов: {len(application.projects or [])}"
        )

        # Telegram уведомление
        try:
            notify_new_application(application)
        except Exception as e:
            logger.error(f"Ошибка Telegram: {e}")

        return Response(
            ApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED,
        )

    # GET: список с фильтрацией
    queryset = Application.objects.all()

    # Фильтр по городу
    city = request.query_params.get('city')
    if city:
        queryset = queryset.filter(city__icontains=city)

    # Фильтр по языку (ищем в JSON массиве)
    language = request.query_params.get('language')
    if language:
        queryset = queryset.filter(languages__contains=[language])

    # Фильтр по статусу
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    # Текстовый поиск
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(telegram_username__icontains=search)
        )

    # Пагинация
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = ApplicationListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET', 'PUT', 'DELETE'])
def application_detail(request, pk):
    """
    GET    /api/applications/<id>/ — детали заявки
    PUT    /api/applications/<id>/ — обновить заявку
    DELETE /api/applications/<id>/ — удалить заявку
    """
    try:
        application = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        return Response(
            {'error': f'Заявка #{pk} не найдена'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == 'GET':
        serializer = ApplicationSerializer(application)
        return Response(serializer.data)

    if request.method == 'PUT':
        serializer = ApplicationSerializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        app_logger.info(f"Заявка #{pk} обновлена")
        return Response(serializer.data)

    if request.method == 'DELETE':
        app_logger.info(f"Заявка #{pk} удалена ({application.name})")
        application.delete()
        return Response(
            {'status': 'deleted', 'id': pk},
            status=status.HTTP_204_NO_CONTENT,
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ГОРОДА И РЕГИОНЫ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['GET'])
def city_list(request):
    """
    GET /api/cities/ — список всех городов Казахстана.
    Фронт использует это для dropdown.
    """
    return Response({
        'cities': get_all_cities(),
        'languages': LANGUAGES_CHOICES,
    })


@api_view(['GET'])
def city_regions(request, city):
    """
    GET /api/cities/<city>/regions/ — регион для указанного города.
    Пример: GET /api/cities/Алматы/regions/ → {"region": "город Алматы"}
    """
    region = get_regions_for_city(city)
    if region is None:
        return Response(
            {'error': f"Город '{city}' не найден"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response({'city': city, 'region': region})





# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# АДМИН АВТОРИЗАЦИЯ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['POST'])
def admin_login(request):
    """
    POST /api/admin/login/ — авторизация админа.

    JSON: {"username": "era", "password": "admin1"}

    Как работает:
      1. Проверяем username == settings.PANEL_USERNAME
      2. Проверяем password через bcrypt.checkpw() vs settings.PANEL_PASSWORD_HASH
      3. Если правильно → сохраняем сессию

    Пароль НИКОГДА не хранится в открытом виде.
    Хеш генерируется командой:
      python -c "import bcrypt; print(bcrypt.hashpw(b'admin1', bcrypt.gensalt()).decode())"
    """
    serializer = AdminLoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']

    expected_user = settings.PANEL_USERNAME
    password_hash = settings.PANEL_PASSWORD_HASH

    # Проверка username
    if username != expected_user:
        logger.warning(f"Неудачная попытка входа: username={username}")
        return Response(
            {'success': False, 'error': 'Неверный логин или пароль'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Проверка пароля через bcrypt
    if not password_hash:
        logger.error("PANEL_PASSWORD_HASH не настроен в .env!")
        return Response(
            {'success': False, 'error': 'Сервер не настроен'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        password_valid = bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8'),
        )
    except Exception as e:
        logger.error(f"Ошибка проверки пароля: {e}")
        return Response(
            {'success': False, 'error': 'Ошибка сервера'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not password_valid:
        logger.warning(f"Неверный пароль для пользователя {username}")
        return Response(
            {'success': False, 'error': 'Неверный логин или пароль'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    # Успех — сохраняем в сессию
    request.session['panel_auth'] = True
    logger.info(f"Успешный вход в админку: {username}")
    return Response({'success': True})


@api_view(['GET'])
def admin_applications(request):
    if not request.session.get('panel_auth'):
        return Response({'error': 'Не авторизован'}, status=status.HTTP_403_FORBIDDEN)

    search = request.query_params.get('search', '')

    try:
        results = _load_from_local_db(search)
        return Response({'count': len(results), 'results': results, 'source': 'local'})
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")
        return Response({'error': str(e)}, status=500)


def _load_from_bot_db(search, funnel, scored):
    """Load from BotApplication (Supabase). Raises on connection error."""
    qs = BotApplication.objects.using('bot_db').all()

    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(telegram_username__icontains=search) |
            Q(city__icontains=search)
        )
    if funnel:
        qs = qs.filter(funnel_stage=funnel)
    if scored == 'true':
        qs = qs.exclude(score_prediction__isnull=True).exclude(score_prediction='')
    elif scored == 'false':
        qs = qs.filter(Q(score_prediction__isnull=True) | Q(score_prediction=''))

    qs = qs.order_by('-id')
    results = []
    for app in qs[:100]:  # this line triggers DB query — raises if unreachable
        results.append(_serialize_bot_app(app))
    return results


def _load_from_local_db(search):
    qs = Application.objects.all().order_by('-created_at')
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(telegram_username__icontains=search) |
            Q(city__icontains=search)
        )

    results = []
    for app in qs[:100]:
        sr = app.scoring_result or {}
        flags = sr.get('flags', {})
        ai_det = flags.get('ai_detection', {})
        # If the ML detector gave an alert/warning or mentions AI probability
        ai_flag = (
            ai_det.get('status') in ('warning', 'alert', 'critical', 'danger') or
            'ИИ' in str(ai_det.get('detail', '')) or
            'AI' in str(ai_det.get('detail', ''))
        )
        results.append({
            'id': app.id,
            'telegram_id': app.telegram_id or 0,
            'telegram_username': app.telegram_username or '',
            'funnel_stage': 'completed',
            'name': app.name or '',
            'age': app.age,
            'city': app.city or '',
            'region': app.region or '',
            'school_type': app.school_type or '',
            'gpa': app.gpa,
            'gpa_raw': app.gpa_raw or '',
            'languages': app.languages or [],
            'ielts_score': '',
            'ent_score': '',
            'olympiads': app.olympiads or [],
            'courses': app.courses or [],
            'projects': app.projects or [],
            'essay_text': app.essay or '',
            'essay_word_count': len((app.essay or '').split()),
            'scenario_choices': {},
            'fingerprint_display': {},
            'fingerprint_reliable': False,
            'timer_violations': 0,
            'score_prediction': sr.get('prediction', ''),
            'score_confidence': sr.get('confidence'),
            'score_probabilities': sr.get('probabilities'),
            'score_explanation': sr.get('explanation'),
            'score_radar': sr.get('radar'),
            'score_flags': flags,
            'ai_detection_flag': ai_flag,
            'scored_at': None,
            'updated_at': str(app.updated_at) if app.updated_at else None,
        })
    return results


def _serialize_bot_app(app):
    """Serialize BotApplication to JSON dict for the admin panel."""
    fp = app.fingerprint_display or {}
    return {
        'id': app.id,
        'telegram_id': app.telegram_id,
        'telegram_username': app.telegram_username or '',
        'funnel_stage': app.funnel_stage or 'started',
        'name': app.name or '',
        'age': app.age,
        'city': app.city or '',
        'region': app.region or '',
        'school_type': app.school_type or '',
        'gpa': app.gpa,
        'gpa_raw': app.gpa_raw or '',
        'languages': app.languages or [],
        'ielts_score': app.ielts_score or '',
        'ent_score': app.ent_score or '',
        'olympiads': app.olympiads or [],
        'courses': app.courses or [],
        'projects': app.projects or [],
        'essay_text': app.essay_text or '',
        'essay_word_count': app.essay_word_count or 0,
        'scenario_choices': app.scenario_choices or {},
        'fingerprint_display': fp,
        'fingerprint_reliable': bool(app.fingerprint_reliable),
        'timer_violations': app.timer_violations or 0,
        # Scoring results (if already scored)
        'score_prediction': app.score_prediction or '',
        'score_confidence': app.score_confidence,
        'score_probabilities': app.score_probabilities,
        'score_explanation': app.score_explanation,
        'score_radar': app.score_radar,
        'score_flags': app.score_flags,
        'ai_detection_flag': (
            (app.score_flags or {}).get('ai_detection', {}).get('status') in ('warning', 'alert', 'critical', 'danger') or
            'ИИ' in str((app.score_flags or {}).get('ai_detection', {}).get('detail', '')) or
            'AI' in str((app.score_flags or {}).get('ai_detection', {}).get('detail', ''))
        ) if app.score_flags else False,
        'scored_at': str(app.scored_at) if app.scored_at else None,
        'updated_at': str(app.updated_at) if app.updated_at else None,
    }


@api_view(['POST'])
def admin_score_application(request, pk):
    """
    POST /api/admin/applications/<id>/score/ — оценить заявку через ML pipeline.
    Пытается: BotApplication (Supabase) → fallback Application (local).
    """
    if not request.session.get('panel_auth'):
        return Response({'error': 'Не авторизован'}, status=status.HTTP_403_FORBIDDEN)

    app = None
    source = None

    # Try BotApplication first
    try:
        app = BotApplication.objects.using('bot_db').get(pk=pk)
        source = 'bot_db'
    except Exception:
        pass

    # Fallback to local Application
    if app is None:
        try:
            app = Application.objects.get(pk=pk)
            source = 'local'
        except Application.DoesNotExist:
            return Response({'error': f'Заявка #{pk} не найдена'}, status=status.HTTP_404_NOT_FOUND)

    try:
        if source == 'bot_db':
            candidate_dict = app.to_pipeline_dict()
        else:
            # Local Application — simple conversion
            candidate_dict = {
                'id': str(app.pk),
                'personal': {'name': app.name or '', 'age': app.age or 18,
                             'city': app.city or '', 'region': app.region or '',
                             'languages': app.languages or [],
                             'school_type': app.school_type or '', 'has_mentor': False},
                'education': {'gpa': app.gpa or 3.5,
                              'olympiads': app.olympiads or [],
                              'courses': app.courses or []},
                'experience': {'projects': app.projects or []},
                'essay': {'text': app.essay or '', 'word_count': len((app.essay or '').split())},
                'motivation': {'text': ''},
                'self_assessment': {},
                'bot_metadata': {},
            }

        result = score_candidate(candidate_dict)

        # Save back to the right DB
        from datetime import datetime
        if source == 'bot_db':
            app.score_prediction = result.get('prediction', '')
            app.score_confidence = result.get('confidence', 0.0)
            app.score_probabilities = result.get('probabilities', {})
            app.score_explanation = result.get('explanation', {})
            app.score_radar = result.get('radar', {})
            app.score_flags = result.get('flags', {})
            app.scored_at = datetime.utcnow()
            app.save(using='bot_db', update_fields=[
                'score_prediction', 'score_confidence', 'score_probabilities',
                'score_explanation', 'score_radar', 'score_flags', 'scored_at',
            ])
        else:
            app.scoring_result = result
            app.save(update_fields=['scoring_result'])

        return Response(result)
    except FileNotFoundError as e:
        return Response({'error': str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        logger.error(f"Ошибка скоринга заявки #{pk}: {e}")
        return Response({'error': f'Ошибка скоринга: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def admin_score_all_applications(request):
    """
    POST /api/admin/applications/score-all/ — оценить все неоценённые заявки.
    Пытается: BotApplication (Supabase) → fallback Application (local).
    """
    if not request.session.get('panel_auth'):
        return Response({'error': 'Не авторизован'}, status=status.HTTP_403_FORBIDDEN)

    from datetime import datetime
    source = None
    unscored = []

    # Try bot_db first
    try:
        qs = BotApplication.objects.using('bot_db').filter(
            Q(score_prediction__isnull=True) | Q(score_prediction='')
        )
        unscored = list(qs[:50])
        source = 'bot_db'
    except Exception:
        pass

    # Fallback to local
    if source is None:
        try:
            qs = Application.objects.filter(scoring_result__isnull=True)
            unscored = list(qs[:50])
            source = 'local'
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    if not unscored:
        return Response({'message': 'Все заявки уже оценены', 'scored': 0})

    scored_count = 0
    errors = []
    for app in unscored:
        try:
            if source == 'bot_db':
                candidate_dict = app.to_pipeline_dict()
            else:
                candidate_dict = {
                    'id': str(app.pk),
                    'personal': {'name': app.name or '', 'age': app.age or 18,
                                 'city': app.city or '', 'region': app.region or '',
                                 'languages': app.languages or [],
                                 'school_type': app.school_type or '', 'has_mentor': False},
                    'education': {'gpa': app.gpa or 3.5,
                                  'olympiads': app.olympiads or [],
                                  'courses': app.courses or []},
                    'experience': {'projects': app.projects or []},
                    'essay': {'text': app.essay or '', 'word_count': len((app.essay or '').split())},
                    'motivation': {'text': ''},
                    'self_assessment': {},
                    'bot_metadata': {},
                }

            result = score_candidate(candidate_dict)

            if source == 'bot_db':
                app.score_prediction = result.get('prediction', '')
                app.score_confidence = result.get('confidence', 0.0)
                app.score_probabilities = result.get('probabilities', {})
                app.score_explanation = result.get('explanation', {})
                app.score_radar = result.get('radar', {})
                app.score_flags = result.get('flags', {})
                app.scored_at = datetime.utcnow()
                app.save(using='bot_db', update_fields=[
                    'score_prediction', 'score_confidence', 'score_probabilities',
                    'score_explanation', 'score_radar', 'score_flags', 'scored_at',
                ])
            else:
                app.scoring_result = result
                app.save(update_fields=['scoring_result'])

            scored_count += 1
        except Exception as e:
            errors.append(f"#{app.pk}: {str(e)}")
            logger.error(f"Ошибка скоринга #{app.pk}: {e}")

    resp = {'message': f'Оценено {scored_count} из {len(unscored)}', 'scored': scored_count}
    if errors:
        resp['errors'] = errors[:5]
    return Response(resp)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# СТАРЫЕ ENDPOINTS — ML pipeline (сохранены)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@api_view(['GET', 'POST'])
def candidate_list_create(request):
    """
    GET:  List all candidates with sorting, filtering, pagination.
    POST: Register a new candidate.
    """
    if request.method == 'POST':
        serializer = CandidateRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate = serializer.save()
        return Response(
            {
                'id': candidate.id,
                'status': 'registered',
                'message': f'Кандидат {candidate.name} успешно зарегистрирован',
            },
            status=status.HTTP_201_CREATED,
        )

    # GET: List with sorting and filtering
    queryset = Candidate.objects.select_related('scoring').all()

    prediction = request.query_params.get('prediction')
    if prediction:
        queryset = queryset.filter(scoring__prediction=prediction)

    city = request.query_params.get('city')
    if city:
        queryset = queryset.filter(city__icontains=city)

    sort_by = request.query_params.get('sort_by', 'created_at')
    order = request.query_params.get('order', 'desc')

    sort_map = {
        'name': 'name',
        'age': 'age',
        'city': 'city',
        'created_at': 'created_at',
        'confidence': 'scoring__confidence',
        'prediction': 'scoring__prediction',
    }

    sort_field = sort_map.get(sort_by, 'created_at')
    if order == 'desc':
        sort_field = f'-{sort_field}'

    queryset = queryset.order_by(sort_field)

    paginator = PageNumberPagination()
    page_size = request.query_params.get('page_size')
    if page_size:
        paginator.page_size = int(page_size)
    page = paginator.paginate_queryset(queryset, request)
    serializer = CandidateListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def candidate_detail(request, pk):
    """Get full details of a candidate including scoring result."""
    try:
        candidate = Candidate.objects.select_related('scoring').get(pk=pk)
    except Candidate.DoesNotExist:
        return Response(
            {'error': 'Кандидат не найден'},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = CandidateDetailSerializer(candidate)
    return Response(serializer.data)


@api_view(['GET'])
def candidate_search(request):
    """Search candidates by name, city, or region."""
    q = request.query_params.get('q', '').strip()
    if not q:
        return Response({'results': []})

    queryset = Candidate.objects.select_related('scoring').filter(
        Q(name__icontains=q) |
        Q(city__icontains=q) |
        Q(region__icontains=q)
    )[:20]

    serializer = CandidateListSerializer(queryset, many=True)
    return Response({'results': serializer.data})


@api_view(['POST'])
def candidate_score(request, pk):
    """Run ML scoring for a candidate."""
    try:
        candidate = Candidate.objects.get(pk=pk)
    except Candidate.DoesNotExist:
        return Response(
            {'error': 'Кандидат не найден'},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        candidate_dict = candidate.to_pipeline_dict()
        result = score_candidate(candidate_dict)

        ScoringResult.objects.update_or_create(
            candidate=candidate,
            defaults={
                'prediction': result['prediction'],
                'confidence': result['confidence'],
                'probabilities': result.get('probabilities', {}),
                'full_result': result,
            },
        )

        return Response(result)

    except FileNotFoundError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except Exception as e:
        return Response(
            {'error': f'Ошибка скоринга: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET'])
def candidate_ranking(request):
    """Get all scored candidates ranked by shortlist probability."""
    scored = ScoringResult.objects.select_related('candidate').all()

    results = []
    for sr in scored:
        shortlist_prob = sr.probabilities.get('shortlist', 0)
        results.append({
            'id': sr.candidate.id,
            'name': sr.candidate.name,
            'city': sr.candidate.city,
            'prediction': sr.prediction,
            'confidence': sr.confidence,
            'shortlist_probability': shortlist_prob,
        })

    results.sort(key=lambda x: x['shortlist_probability'], reverse=True)

    for i, r in enumerate(results):
        r['rank'] = i + 1
        r['total_candidates'] = len(results)

    return Response({'results': results})


@api_view(['POST'])
def score_all(request):
    """Score all candidates that haven't been scored yet."""
    unscored = Candidate.objects.filter(scoring__isnull=True)
    count = unscored.count()

    if count == 0:
        return Response({'message': 'Все кандидаты уже оценены', 'scored': 0})

    try:
        scored_count = 0
        for candidate in unscored:
            candidate_dict = candidate.to_pipeline_dict()
            result = score_candidate(candidate_dict)

            ScoringResult.objects.update_or_create(
                candidate=candidate,
                defaults={
                    'prediction': result['prediction'],
                    'confidence': result['confidence'],
                    'probabilities': result.get('probabilities', {}),
                    'full_result': result,
                },
            )
            scored_count += 1

        return Response({
            'message': f'Оценено {scored_count} кандидатов',
            'scored': scored_count,
        })

    except Exception as e:
        return Response(
            {'error': f'Ошибка: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['GET', 'POST'])
def teacher_nominations(request):
    """
    GET  /api/teacher/nominations/ — список рекомендаций текущего учителя
    POST /api/teacher/nominations/ — добавить рекомендацию ученика

    Требует session['teacher_auth'].
    """
    teacher_login = request.session.get('teacher_auth')
    if not teacher_login:
        return Response({'error': 'Не авторизован'}, status=status.HTTP_403_FORBIDDEN)

    teacher_name = request.session.get('teacher_name', teacher_login)

    if request.method == 'GET':
        nominations = TeacherNomination.objects.filter(teacher_login=teacher_login)
        data = [{
            'id': n.id,
            'student_name': n.student_name,
            'student_contacts': n.student_contacts,
            'reason': n.reason,
            'achievements': n.achievements,
            'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
        } for n in nominations]
        return Response({'count': len(data), 'results': data})

    # POST — create nomination
    student_name = request.data.get('student_name', '').strip()
    student_contacts = request.data.get('student_contacts', '').strip()
    reason = request.data.get('reason', '').strip()
    achievements = request.data.get('achievements', '').strip()

    if not student_name or not student_contacts or not reason:
        return Response(
            {'error': 'ФИО, контакты и обоснование обязательны'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    nomination = TeacherNomination.objects.create(
        teacher_login=teacher_login,
        teacher_name=teacher_name,
        student_name=student_name,
        student_contacts=student_contacts,
        reason=reason,
        achievements=achievements,
    )
    logger.info(f"Учитель {teacher_login} рекомендовал ученика: {student_name}")
    return Response({
        'id': nomination.id,
        'student_name': nomination.student_name,
        'student_contacts': nomination.student_contacts,
        'reason': nomination.reason,
        'achievements': nomination.achievements,
        'status': nomination.status,
        'admin_note': nomination.admin_note,
        'created_at': nomination.created_at.strftime('%d.%m.%Y %H:%M'),
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def admin_nominations_list(request):
    if not request.session.get('panel_auth'):
        return Response({'error': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    nominations = TeacherNomination.objects.all().order_by('-created_at')
    data = [{
        'id': n.id,
        'teacher_login': n.teacher_login,
        'teacher_name': n.teacher_name,
        'student_name': n.student_name,
        'student_contacts': n.student_contacts,
        'reason': n.reason,
        'achievements': n.achievements,
        'status': n.status,
        'admin_note': n.admin_note,
        'created_at': n.created_at.strftime('%d.%m.%Y %H:%M'),
    } for n in nominations]
    return Response({'count': len(data), 'results': data})


@api_view(['POST'])
def admin_nomination_review(request, pk):
    if not request.session.get('panel_auth'):
        return Response({'error': 'Нет доступа'}, status=status.HTTP_403_FORBIDDEN)
    try:
        nomination = TeacherNomination.objects.get(pk=pk)
    except TeacherNomination.DoesNotExist:
        return Response({'error': 'Не найдено'}, status=status.HTTP_404_NOT_FOUND)
    new_status = request.data.get('status')
    if new_status not in ('accepted', 'rejected', 'pending'):
        return Response({'error': 'Статус: accepted | rejected | pending'}, status=status.HTTP_400_BAD_REQUEST)
    nomination.status = new_status
    nomination.admin_note = request.data.get('admin_note', nomination.admin_note)
    nomination.save()
    return Response({'id': nomination.id, 'status': nomination.status, 'admin_note': nomination.admin_note})
