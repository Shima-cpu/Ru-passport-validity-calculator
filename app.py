# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

st.set_page_config(
    page_title="Калькулятор замены паспорта РФ",
    page_icon="🛂",
    layout="centered",
)

# ===== Диапазоны выбора дат =====
MIN_BIRTH = date(1900, 1, 1)
MAX_BIRTH = date.today()
MIN_ISSUE = date(1900, 1, 1)
MAX_ISSUE = date.today()

# ===== Хелперы =====
def safe_add_years(d: date, years: int) -> date:
    """Добавить годы к дате, корректно обрабатывая 29 февраля."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(month=2, day=28, year=d.year + years)

def current_passport_stage(birth: date, issue: date) -> int | None:
    """
    Определить этап текущего паспорта по дате выдачи:
    возвращает 14, 20, 45 или None (если ввод странный).
    """
    d14 = safe_add_years(birth, 14)
    d20 = safe_add_years(birth, 20)
    d45 = safe_add_years(birth, 45)

    if issue >= d45:
        return 45
    if d20 <= issue <= d45 + timedelta(days=90):
        return 20
    if d14 <= issue <= d20 + timedelta(days=90):
        return 14
    return None

def classify_passport_stage_text(stage: int | None) -> str:
    if stage == 14:
        return "Первичное получение в 14 лет"
    if stage == 20:
        return "Обмен в 20 лет"
    if stage == 45:
        return "Обмен в 45 лет"
    return "Не удалось однозначно определить (проверьте ввод)"

def compute_status(birth: date, issue: date, today: date) -> dict:
    """
    Возвращает:
      stage_label, next_change, deadline,
      status_kind: 'invalid' | 'due' | 'ok' | 'no_more',
      days_left (если применимо).
    """
    d20 = safe_add_years(birth, 20)
    d45 = safe_add_years(birth, 45)

    stage = current_passport_stage(birth, issue)
    stage_label = classify_passport_stage_text(stage)

    if stage == 45:
        return {
            "stage_label": stage_label,
            "next_change": None,
            "deadline": None,
            "status_kind": "no_more",
            "days_left": None,
        }

    if stage == 20:
        next_change = d45
    elif stage == 14:
        next_change = d20
    else:
        # не смогли определить — подстрахуемся по возрасту
        next_change = d20 if today < d45 else d45

    deadline = next_change + timedelta(days=90)

    if today > deadline:
        status_kind = "invalid"            # просрочено > 90 дней
        days_left = None
    elif today >= next_change:
        status_kind = "due"                # порог наступил, но дедлайн ещё не прошёл
        days_left = (deadline - today).days
    else:
        status_kind = "ok"                 # до порога ещё не дошли
        days_left = (next_change - today).days

    return {
        "stage_label": stage_label,
        "next_change": next_change,
        "deadline": deadline,
        "status_kind": status_kind,
        "days_left": days_left,
    }

def validate_inputs(birth: date, issue: date, today: date) -> list[str]:
    errs: list[str] = []

    if birth > today:
        errs.append("Дата рождения не может быть в будущем.")
    if issue > today:
        errs.append("Дата выдачи паспорта не может быть в будущем.")
    if issue < birth:
        errs.append("Дата выдачи паспорта не может быть раньше даты рождения.")

    if relativedelta(today, birth).years < 14:
        errs.append("Лицу младше 14 лет паспорт ещё не выдается.")

    d14 = safe_add_years(birth, 14)
    if issue < d14:
        errs.append("Паспорт не может быть выдан ранее достижения 14 лет. Проверьте дату выдачи.")

    if not (MIN_BIRTH <= birth <= MAX_BIRTH):
        errs.append(
            f"Дата рождения должна быть в диапазоне "
            f"{MIN_BIRTH.strftime('%d.%m.%Y')}–{MAX_BIRTH.strftime('%d.%m.%Y')}."
        )
    if not (MIN_ISSUE <= issue <= MAX_ISSUE):
        errs.append(
            f"Дата выдачи должна быть в диапазоне "
            f"{MIN_ISSUE.strftime('%d.%m.%Y')}–{MAX_ISSUE.strftime('%d.%m.%Y')}."
        )

    return errs

# ===== UI =====
st.title("🛂 Калькулятор замены паспорта РФ")
st.caption("Рассчитывает даты обязательной замены по порогам 20 и 45 лет и 90-дневному сроку после дня рождения.")

with st.expander("Правовая основа (кратко)"):
    st.markdown(
        "- Паспорт гражданина РФ выдаётся в 14 лет и подлежит замене при достижении 20 и 45 лет.\n"
        "- На замену предоставляется 90 календарных дней после соответствующего дня рождения.\n"
        "⚠️ Учитывайте, что локальные правила/исключения (например, замена за рубежом) могут меняться."
    )

today = date.today()
col1, col2 = st.columns(2)
with col1:
    birth = st.date_input(
        "Дата рождения",
        value=date(1990, 1, 1),
        min_value=MIN_BIRTH,
        max_value=MAX_BIRTH,
        format="DD.MM.YYYY",   # если старая версия Streamlit — удалите этот параметр
        key="birth_v4",
    )
with col2:
    issue = st.date_input(
        "Дата выдачи текущего паспорта",
        value=date(2010, 1, 1),
        min_value=MIN_ISSUE,
        max_value=MAX_ISSUE,
        format="DD.MM.YYYY",
        key="issue_v4",
    )

if st.button("Рассчитать"):
    errors = validate_inputs(birth, issue, today)
    for e in errors:
        st.error(e)

    if not errors:
        age_years = relativedelta(today, birth).years
        st.subheader("Результаты")
        st.write(f"**Возраст (полных лет):** {age_years}")

        res = compute_status(birth, issue, today)
        st.write(f"**Текущий документ получен как:** {res['stage_label']}")

        if res["next_change"]:
            st.write(f"**Дата обязательной замены:** {res['next_change'].strftime('%d.%m.%Y')}")
            st.write(f"**Крайний срок (90 дней после ДР):** {res['deadline'].strftime('%d.%m.%Y')}")

        # ---- Статус ----
        if res["status_kind"] == "invalid":
            st.error("Паспорт недействителен. Требуется замена.")
        elif res["status_kind"] == "due":
            st.warning(f"Требуется замена. До крайнего срока осталось {res['days_left']} дн.")
        elif res["status_kind"] == "ok":
            st.success(f"Паспорт действителен. До даты замены осталось {res['days_left']} дн.")
        elif res["status_kind"] == "no_more":
            st.info("Возрастных замен больше нет.")
