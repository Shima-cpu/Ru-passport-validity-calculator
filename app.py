# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(
    page_title="Калькулятор замены паспорта РФ",
    page_icon="🛂",
    layout="centered",
)

# ===== Настройки диапазонов дат =====
# При желании сузьте границы (например, MIN_ISSUE = date(1940, 1, 1))
MIN_BIRTH = date(1900, 1, 1)
MAX_BIRTH = date.today()

MIN_ISSUE = date(1900, 1, 1)
MAX_ISSUE = date.today()


# ===== Вспомогательные функции =====
def safe_add_years(d: date, years: int) -> date:
    """Добавить годы к дате рождения, корректно обрабатывая 29 февраля."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        # Если 29 февраля -> берём 28 февраля соответствующего года
        return d.replace(month=2, day=28, year=d.year + years)


def classify_passport_stage(birth: date, issue: date) -> str:
    """Определить, на каком возрастном этапе был выдан ТЕКУЩИЙ паспорт."""
    d14 = safe_add_years(birth, 14)
    d20 = safe_add_years(birth, 20)
    d45 = safe_add_years(birth, 45)

    # Допускаем 90-дневный коридор после пороговой даты рождения
    if d14 <= issue <= d20 + timedelta(days=90):
        return "Первичное получение в 14 лет"
    if d20 <= issue <= d45 + timedelta(days=90):
        return "Обмен в 20 лет"
    if issue >= d45:
        return "Обмен в 45 лет"
    return "Необычная дата выдачи (проверьте ввод)"


def compute_next_change(birth: date, today: date) -> dict:
    """Рассчитать следующую обязательную замену и крайний срок (90 дней)."""
    d20 = safe_add_years(birth, 20)
    d45 = safe_add_years(birth, 45)

    if today < d20:
        stage = "Первая замена в 20 лет"
        next_change = d20
    elif today < d45:
        stage = "Вторая замена в 45 лет"
        next_change = d45
    else:
        return {
            "stage": "После 45 лет: возрастных замен больше нет",
            "next_change": None,
            "deadline": None,
            "status": "После 45 лет паспорт считается бессрочным (без возрастных замен).",
        }

    deadline = next_change + timedelta(days=90)
    if today > deadline:
        status = "❌ Срок замены просрочен (прошло более 90 дней после дня рождения)."
    elif today >= next_change:
        days = (deadline - today).days
        status = f"⚠️ Требуется замена. До крайнего срока осталось {days} дн."
    else:
        days = (next_change - today).days
        status = f"✅ Паспорт действителен. До даты замены осталось {days} дн."

    return {
        "stage": stage,
        "next_change": next_change,
        "deadline": deadline,
        "status": status,
    }


def validate_inputs(birth: date, issue: date, today: date) -> list[str]:
    """Базовые проверки валидности ввода."""
    errs = []

    # Общие проверки
    if birth > today:
        errs.append("Дата рождения не может быть в будущем.")
    if issue > today:
        errs.append("Дата выдачи паспорта не может быть в будущем.")
    if issue < birth:
        errs.append("Дата выдачи паспорта не может быть раньше даты рождения.")

    # Возраст < 14 лет — паспорт ещё не выдается
    if relativedelta(today, birth).years < 14:
        errs.append("Лицу младше 14 лет паспорт ещё не выдается.")

    # Выдача раньше 14-летия — некорректно
    d14 = safe_add_years(birth, 14)
    if issue < d14:
        errs.append("Паспорт не может быть выдан ранее достижения 14 лет. Проверьте дату выдачи.")

    # Границы виджета (доп.проверка — на случай ручной правки через query params)
    if not (MIN_BIRTH <= birth <= MAX_BIRTH):
        errs.append(f"Дата рождения должна быть в диапазоне {MIN_BIRTH.strftime('%d.%m.%Y')}–{MAX_BIRTH.strftime('%d.%m.%Y')}.")
    if not (MIN_ISSUE <= issue <= MAX_ISSUE):
        errs.append(f"Дата выдачи должна быть в диапазоне {MIN_ISSUE.strftime('%d.%m.%Y')}–{MAX_ISSUE.strftime('%d.%m.%Y')}.")

    return errs


# ===== UI =====
st.title("🛂 Калькулятор замены паспорта РФ")
st.caption("Вычисляет даты обязательной замены по порогам 20 и 45 лет и 90-дневному сроку после дня рождения.")

with st.expander("Правовая основа (кратко)"):
    st.markdown(
        "- Паспорт гражданина РФ выдаётся в 14 лет и подлежит замене при достижении 20 и 45 лет.\n"
        "- На замену предоставляется 90 календарных дней после соответствующего дня рождения.\n"
        "⚠️ Учитывайте, что локальные правила/исключения (например, за рубежом) могут меняться."
    )

today = date.today()
col1, col2 = st.columns(2)

with col1:
    birth = st.date_input(
        "Дата рождения",
        value=date(1990, 1, 1),
        min_value=MIN_BIRTH,
        max_value=MAX_BIRTH,
        format="DD.MM.YYYY",  # Если у вас старая версия Streamlit и будет ошибка — удалите этот параметр
        key="birth_v2",       # Новый ключ во избежание «залипания» старых ограничений
    )

with col2:
    issue = st.date_input(
        "Дата выдачи текущего паспорта",
        value=date(2010, 1, 1),
        min_value=MIN_ISSUE,
        max_value=MAX_ISSUE,
        format="DD.MM.YYYY",
        key="issue_v2",       # Новый ключ
    )

if st.button("Рассчитать"):
    errors = validate_inputs(birth, issue, today)
    for e in errors:
        st.error(e)

    if not errors:
        age_years = relativedelta(today, birth).years
        st.subheader("Результаты")
        st.write(f"**Возраст (полных лет):** {age_years}")

        stage_info = classify_passport_stage(birth, issue)
        st.write(f"**Текущий документ получен как:** {stage_info}")

        res = compute_next_change(birth, today)
        st.write(f"**Этап:** {res['stage']}")

        if res["next_change"]:
            st.write(f"**Дата обязательной замены:** {res['next_change'].strftime('%d.%m.%Y')}")
            st.write(f"**Крайний срок (90 дней после ДР):** {res['deadline'].strftime('%d.%m.%Y')}")
        st.info(res["status"])

        # Подсказки и несоответствия
        d20 = safe_add_years(birth, 20)
        d45 = safe_add_years(birth, 45)
        if issue < d20 and age_years >= 20:
            st.warning(
                "Дата выдачи указывает на документ, полученный до 20 лет, "
                "но возраст уже 20+. Вероятно, документ должен был быть заменён в 20 лет."
            )
        if issue < d45 and age_years >= 45:
            st.warning(
                "Дата выдачи указывает на документ, полученный до 45 лет, "
                "но возраст уже 45+. Вероятно, документ должен был быть заменён в 45 лет."
            )
