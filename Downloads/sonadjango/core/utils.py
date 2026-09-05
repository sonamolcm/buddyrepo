import re
SKILLS = [
    "Python",
    "Django",
    "Java",
    "JavaScript",
    "React",
    "Node.js",
    "HTML",
    "CSS",
    "MySQL",
    "MongoDB",
    "SQLite",
    "Git",
    "AWS",
    "Docker",
    "REST API",
    "C",
    "C++"
]
def extract_email(text):

    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    if match:
        return match.group()

    return ""
def extract_phone(text):

    match = re.search(
        r"(\+91[- ]?)?[6-9]\d{9}",
        text
    )

    if match:
        return match.group()

    return ""
def extract_skills(text):

    found_skills = []

    text = text.lower()

    for skill in SKILLS:

        if skill.lower() in text:
            found_skills.append(skill)

    return found_skills
def extract_experience(text):

    match = re.search(
        r"(\d+)\+?\s*(year|years)",
        text,
        re.IGNORECASE
    )

    if match:
        return match.group()

    return ""
def extract_education(text):

    education_list = [
        "B.Tech",
        "B.E",
        "M.Tech",
        "MCA",
        "BCA",
        "B.Sc",
        "M.Sc",
        "MBA"
    ]

    for education in education_list:

        if education.lower() in text.lower():
            return education

    return ""