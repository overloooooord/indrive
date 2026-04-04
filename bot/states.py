from aiogram.fsm.state import State, StatesGroup


class ConsentState(StatesGroup):
    waiting = State()


class PersonalState(StatesGroup):
    name = State()
    age = State()
    city = State()
    region = State()


class EducationState(StatesGroup):
    school_type = State()
    languages = State()
    gpa = State()
    # IELTS / ENT
    ielts_score = State()
    ielts_doc = State()
    ent_score = State()
    ent_doc = State()
    cert_upload = State()
    # Olympiads
    olympiad_filter = State()
    olympiad_subject = State()
    olympiad_year = State()
    olympiad_level = State()
    olympiad_prize = State()
    olympiad_loop = State()
    # Courses
    course_filter = State()
    course_name = State()
    course_platform = State()
    course_year = State()
    course_completed = State()
    course_loop = State()


class ExperienceState(StatesGroup):
    filter = State()
    name = State()
    type = State()
    year = State()
    role = State()
    team_size = State()
    description = State()
    failure_filter = State()
    failure_note = State()
    continued = State()
    loop = State()


class EssayState(StatesGroup):
    writing = State()


class ScenarioState(StatesGroup):
    intro = State()
    answering = State()
    step_1 = State()
    step_2a = State()
    step_2b = State()
    step_2c = State()
    step_2d = State()
    step_3 = State()
    step_4 = State()
    done = State()


class FileUploadState(StatesGroup):
    waiting = State()
