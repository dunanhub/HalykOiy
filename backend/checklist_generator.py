CHECKLIST_RULES = {
    "all": [
        {"item": "Паспорт / удостоверение личности", "icon": "🪪", "required": True},
        {"item": "Телефон + зарядка", "icon": "📱", "required": True},
        {"item": "Банковская карта Halyk", "icon": "💳", "required": True},
        {"item": "Билеты (в приложении Halyk)", "icon": "✈️", "required": True},
        {"item": "Бронь отеля", "icon": "🏨", "required": True},
    ],
    "ребёнок": [
        {"item": "Свидетельство о рождении", "icon": "📄", "required": True},
        {"item": "Страховой полис", "icon": "🛡️", "required": True},
        {"item": "Детское жаропонижающее", "icon": "💊", "required": True},
        {"item": "Любимая игрушка / планшет", "icon": "🧸", "required": False},
        {"item": "Запасная одежда", "icon": "👕", "required": True},
    ],
    "ребёнок_до_3": [
        {"item": "Детское питание / смесь", "icon": "🍼", "required": True},
        {"item": "Подгузники", "icon": "🧷", "required": True},
        {"item": "Коляска / переноска", "icon": "🪑", "required": False},
    ],
}


def default_family_members() -> list[dict]:
    return [
        {"role": "взрослый", "age": None, "name": None},
        {"role": "взрослый", "age": None, "name": None},
        {"role": "ребёнок", "age": None, "name": None},
        {"role": "ребёнок", "age": None, "name": None},
    ]


def generate_checklist(family_members: list[dict]) -> list[dict]:
    checklist = []

    for member in family_members:
        role = member.get("role", "взрослый")
        age = member.get("age")
        name = member.get("name")

        display = name or role.capitalize()
        if age is not None:
            display += f" ({age} л)"

        icon = {
            "папа": "👨",
            "мама": "👩",
            "ребёнок": "🧒",
            "взрослый": "👤",
        }.get(role, "👤")

        items = list(CHECKLIST_RULES["all"])

        if role == "ребёнок":
            items += CHECKLIST_RULES["ребёнок"]
            if age is not None and age < 3:
                items += CHECKLIST_RULES["ребёнок_до_3"]

        checklist.append(
            {
                "member": display,
                "icon": icon,
                "role": role,
                "items": [{**item, "checked": False} for item in items],
            }
        )

    return checklist


def default_family_checklist() -> list[dict]:
    return generate_checklist(default_family_members())
