from __future__ import annotations

import dataclasses
import datetime
import typing
import xml.etree.ElementTree as ET

import pytz

from .shared import parse_free_days, parse_plan_date, Value, Exam

# Cache timezone at module import to avoid blocking I/O in event loop
_BERLIN_TZ = pytz.timezone("Europe/Berlin")

__all__ = [
    "IndiwareMobilPlan",
    "Form",
    "Lesson",
    "Class"
]


class IndiwareMobilPlan:
    plan_type: str
    timestamp: datetime.datetime | None  # time of last update
    date: datetime.date
    filename: str
    native: str
    week: int
    days_per_week: int
    school_number: int = None

    free_days: list[datetime.date]
    forms: list[Form]
    additional_info: list[str]

    @classmethod
    def from_xml(cls, xml: ET.Element):
        day = cls()

        # parse head
        head = xml.find("Kopf")
        day.plan_type = head.find("planart").text

        day.timestamp = (
            _BERLIN_TZ.localize(datetime.datetime.strptime(head.find("zeitstempel").text, "%d.%m.%Y, %H:%M"))
        ) if head.find("zeitstempel") is not None else None
        day.date = parse_plan_date(head.find("DatumPlan").text)
        day.filename = head.find("datei").text
        day.native = int(nativ.text) if (nativ := head.find("nativ")) is not None else None
        day.week = int(head.find("woche").text) if head.find("woche") is not None else None
        day.days_per_week = int(head.find("tageprowoche").text) if head.find("tageprowoche") is not None else 5
        try:
            day.school_number = int(head.find("schulnummer").text)
        except (AttributeError, TypeError):
            day.school_number = None

        # parse free days
        ft_tag = xml.find("FreieTage")
        day.free_days = parse_free_days(ft_tag) if ft_tag is not None else []

        # parse classes
        day.forms = []
        for class_ in xml.find("Klassen"):
            day.forms.append(Form.from_xml(class_))

        # parse additional info
        day.additional_info = []
        _additional_info = xml.find("ZusatzInfo")
        _additional_info = _additional_info if _additional_info is not None else []
        for line in _additional_info:
            day.additional_info.append(line.text)

        return day


class Form:
    short_name: str
    hash: str | None

    periods: dict[int, tuple[datetime.time, datetime.time]]
    courses: dict[str, str]  # course name: teacher
    classes: dict[str, Class]
    lessons: list[Lesson]
    exams: list[Exam]
    break_supervisions: list[BreakSupervision]

    @classmethod
    def from_xml(cls, xml: ET.Element):
        form = cls()

        form.short_name = xml.find("Kurz").text
        try:
            form.hash = xml.find("Hash").text
        except AttributeError:
            form.hash = None

        # parse periods
        form.periods = {}
        kl_stunden = xml.find("KlStunden")
        for period in (kl_stunden if kl_stunden is not None else []):
            start, end = period.attrib["ZeitVon"].strip(), period.attrib["ZeitBis"].strip()
            try:
                start = datetime.datetime.strptime(start, "%H:%M").time()
            except ValueError:
                continue
            try:
                end = datetime.datetime.strptime(end, "%H:%M").time()
            except ValueError:
                continue
            form.periods |= {int(period.text): (start, end)}

        # parse courses
        form.courses = {}
        kurse = xml.find("Kurse")
        for _course in (kurse if kurse is not None else []):
            course = _course.find("KKz")
            form.courses |= {course.text: course.attrib["KLe"]}

        # parse classes
        form.classes = {}
        unterricht = xml.find("Unterricht")
        for _class in (unterricht if unterricht is not None else []):
            class_ = _class.find("UeNr")
            class_obj = Class(
                teacher=class_.attrib["UeLe"],
                subject=class_.attrib["UeFa"],
                group=class_.attrib["UeGr"] if "UeGr" in class_.attrib else None
            )
            form.classes |= {class_.text: class_obj}

        # parse lessons
        form.lessons = []
        for _lesson in xml.find("Pl"):
            form.lessons.append(Lesson.from_xml(_lesson))

        # parse exams
        form.exams = []
        klausuren = xml.find("Klausuren")
        for _exam in (klausuren if klausuren is not None else []):
            form.exams.append(Exam.from_xml_indiware_mobile(_exam))

        # parse break supervisions
        form.break_supervisions = []
        aufsichten = xml.find("Aufsichten")
        for _break_supervision in (aufsichten if aufsichten is not None else []):
            form.break_supervisions.append(BreakSupervision.from_xml(_break_supervision))

        return form


@dataclasses.dataclass
class Class:
    teacher: str
    subject: str
    group: str | None


BREAK_SUPERVISION_SUBSTITUTION = "AuVertretung"
BREAK_SUPERVISION_CANCELLED = "AuAusfall"


class BreakSupervision:
    status: str | None
    day: int
    before_period: int
    clock_time: datetime.time
    time_label: str
    location: str
    instead_of: str | None
    information: str | None

    @classmethod
    def from_xml(cls, xml: ET.Element) -> typing.Self:
        out = cls()

        out.status = xml.get("AuAe")

        out.day = int(xml.find("AuTag").text)
        out.before_period = int(xml.find("AuVorStunde").text)
        out.clock_time = datetime.datetime.strptime(xml.find("AuUhrzeit").text, "%H:%M").time()
        out.time_label = xml.find("AuZeit").text
        out.location = xml.find("AuOrt").text

        out.instead_of = for_.text if (for_ := xml.find("AuFuer")) is not None else None
        out.information = info.text if (info := xml.find("AuInfo")) is not None else None

        return out


class Lesson:
    period: int
    start: datetime.time
    end: datetime.time

    subject: Value
    teacher: Value
    room: Value

    course2: str | None

    class_number: str | None
    information: str

    @classmethod
    def from_xml(cls, xml: ET.Element):
        lesson = cls()

        lesson.period = int(xml.find("St").text)
        lesson.start = (datetime.datetime.strptime(beg.text.strip().replace(".", ":"), "%H:%M").time()
                        if (beg := xml.find("Beginn")) is not None and beg.text else None)
        lesson.end = (datetime.datetime.strptime(end.text.strip().replace(".", ":"), "%H:%M").time()
                      if (end := xml.find("Ende")) is not None and end.text else None)

        lesson.subject = Value(xml.find("Fa").text, xml.find("Fa").get("FaAe") == "FaGeaendert")
        lesson.teacher = Value(xml.find("Le").text, xml.find("Le").get("LeAe") == "LeGeaendert")
        lesson.room = Value(xml.find("Ra").text, xml.find("Ra").get("RaAe") == "RaGeaendert")

        lesson.course2 = ku2.text if (ku2 := xml.find("Ku2")) is not None else None

        try:
            lesson.class_number = xml.find("Nr").text
        except AttributeError:
            lesson.class_number = None
        lesson.information = xml.find("If").text.strip() if xml.find("If").text is not None else None

        return lesson
