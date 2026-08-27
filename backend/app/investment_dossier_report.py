from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
import re
import unicodedata

import pymupdf


PAGE_WIDTH = 595
PAGE_HEIGHT = 842

MARGIN_LEFT = 50
MARGIN_RIGHT = 50
MARGIN_TOP = 42
MARGIN_BOTTOM = 44

BLACK = (0, 0, 0)
DARK_GRAY = (0.25, 0.25, 0.25)
MEDIUM_GRAY = (0.50, 0.50, 0.50)
LIGHT_GRAY = (0.88, 0.88, 0.88)
VERY_LIGHT_GRAY = (0.96, 0.96, 0.96)
WHITE = (1, 1, 1)


INVESTOR_LABELS = {
    "personne_physique": "Personne physique",
    "societe_existante": "Société existante",
    "societe_en_creation": "Société en création",
}

LAND_LABELS = {
    "proprietaire": "Propriétaire",
    "locataire": "Locataire",
    "demande_attribution": "Demande d'attribution",
    "non_identifie": "Non identifié",
}

WORK_LABELS = {
    "construction": "Construction",
    "extension": "Extension",
    "modification": "Modification ou réaménagement",
    "lotissement_morcellement": "Lotissement ou morcellement",
}

REQUIRED_LEVELS = {
    "obligatoire",
    "required",
}

CONDITIONAL_LEVELS = {
    "conditionnelle",
    "conditional",
}

RECOMMENDED_LEVELS = {
    "recommandee",
    "recommended",
}

PRESENT_STATUSES = {
    "presente_non_verifiee",
    "presente",
    "present",
}

MISSING_STATUSES = {
    "manquante",
    "missing",
}

RECOMMENDED_ABSENT_STATUSES = {
    "recommandee_absente",
    "recommended_absent",
}


def enum_value(value) -> str:
    if value is None:
        return ""

    return str(
        getattr(
            value,
            "value",
            value,
        )
    ).strip()


def optional_value(
    value,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    if text.lower() in {
        "non précisé",
        "non précisée",
        "non detecte",
        "non détecté",
        "none",
        "null",
    }:
        return None

    return text


def pdf_safe_text(
    value,
) -> str:
    if value is None:
        return ""

    text = str(value)

    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }

    for source, target in replacements.items():
        text = text.replace(
            source,
            target,
        )

    text = unicodedata.normalize(
        "NFKC",
        text,
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    return text.encode(
        "cp1252",
        errors="replace",
    ).decode(
        "cp1252",
    ).strip()


def sanitize_filename(
    value: str,
) -> str:
    normalized = unicodedata.normalize(
        "NFKD",
        value,
    )

    ascii_value = "".join(
        character
        for character in normalized
        if not unicodedata.combining(
            character
        )
    )

    ascii_value = ascii_value.encode(
        "ascii",
        errors="ignore",
    ).decode("ascii")

    ascii_value = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        ascii_value,
    ).strip("_")

    return (
        ascii_value[:60]
        or "projet"
    )


def format_amount(
    value,
) -> str | None:
    if value is None:
        return None

    try:
        amount = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return optional_value(value)

    if amount <= 0:
        return None

    return (
        f"{amount:,.0f}"
        .replace(",", " ")
        + " DH"
    )


def convert_payload_to_object(
    value,
):
    if isinstance(value, dict):
        return SimpleNamespace(
            **{
                str(key):
                    convert_payload_to_object(
                        nested_value
                    )
                for key, nested_value
                in value.items()
            }
        )

    if isinstance(value, list):
        return [
            convert_payload_to_object(item)
            for item in value
        ]

    return value


def validate_report_payload(
    raw_payload: dict,
):
    if not isinstance(
        raw_payload,
        dict,
    ):
        raise ValueError(
            "Le résultat transmis doit être "
            "un objet JSON."
        )

    response = convert_payload_to_object(
        raw_payload
    )

    try:
        audit = response.audit
        profile = audit.project_profile
        results = audit.results

        if not isinstance(
            results,
            list,
        ):
            raise TypeError

        getattr(
            profile,
            "sector",
        )

        getattr(
            profile,
            "region",
        )

    except (
        AttributeError,
        TypeError,
    ) as error:
        raise ValueError(
            "Le résultat transmis est incomplet "
            "ou possède une structure invalide."
        ) from error

    return response


def wrap_text(
    text: str,
    max_width: float,
    font_name: str,
    font_size: float,
) -> list[str]:
    safe_text = pdf_safe_text(
        text
    )

    if not safe_text:
        return [""]

    words = safe_text.split()
    lines: list[str] = []
    current_line = ""

    for word in words:
        candidate = (
            word
            if not current_line
            else f"{current_line} {word}"
        )

        candidate_width = (
            pymupdf.get_text_length(
                candidate,
                fontname=font_name,
                fontsize=font_size,
            )
        )

        if (
            candidate_width <= max_width
            or not current_line
        ):
            current_line = candidate
            continue

        lines.append(
            current_line
        )

        current_line = word

    if current_line:
        lines.append(
            current_line
        )

    return lines


def attr(
    value,
    name: str,
    default=None,
):
    return getattr(
        value,
        name,
        default,
    )


class ProfessionalPdfWriter:
    def __init__(
        self,
        document: pymupdf.Document,
    ) -> None:
        self.document = document
        self.page: pymupdf.Page | None = None
        self.y = MARGIN_TOP

    @property
    def content_width(
        self,
    ) -> float:
        return (
            PAGE_WIDTH
            - MARGIN_LEFT
            - MARGIN_RIGHT
        )

    def new_page(
        self,
        *,
        continuation: bool = False,
    ) -> None:
        self.page = self.document.new_page(
            width=PAGE_WIDTH,
            height=PAGE_HEIGHT,
        )

        self.y = MARGIN_TOP

        if continuation:
            assert self.page is not None

            self.page.insert_text(
                (
                    MARGIN_LEFT,
                    27,
                ),
                (
                    "Dossier d'investissement "
                    "- Synthèse du projet"
                ),
                fontname="hebo",
                fontsize=8.5,
                color=BLACK,
            )

            self.page.draw_line(
                (
                    MARGIN_LEFT,
                    34,
                ),
                (
                    PAGE_WIDTH
                    - MARGIN_RIGHT,
                    34,
                ),
                color=MEDIUM_GRAY,
                width=0.6,
            )

            self.y = 53

    def ensure_space(
        self,
        required_height: float,
    ) -> None:
        if self.page is None:
            self.new_page()

        if (
            self.y
            + required_height
            > PAGE_HEIGHT
            - MARGIN_BOTTOM
        ):
            self.new_page(
                continuation=True,
            )

    def add_document_header(
        self,
        title: str,
        subtitle: str | None,
    ) -> None:
        if self.page is None:
            self.new_page()

        assert self.page is not None

        self.page.insert_text(
            (
                MARGIN_LEFT,
                self.y,
            ),
            pdf_safe_text(title),
            fontname="hebo",
            fontsize=17,
            color=BLACK,
        )

        self.y += 25

        if subtitle:
            subtitle_lines = wrap_text(
                subtitle,
                self.content_width,
                "helv",
                9.5,
            )

            for line in subtitle_lines:
                self.page.insert_text(
                    (
                        MARGIN_LEFT,
                        self.y,
                    ),
                    line,
                    fontname="helv",
                    fontsize=9.5,
                    color=DARK_GRAY,
                )

                self.y += 14

        self.page.draw_line(
            (
                MARGIN_LEFT,
                self.y + 4,
            ),
            (
                PAGE_WIDTH
                - MARGIN_RIGHT,
                self.y + 4,
            ),
            color=BLACK,
            width=1.0,
        )

        self.y += 25

    def add_section_title(
        self,
        number: int,
        title: str,
    ) -> None:
        self.ensure_space(38)

        assert self.page is not None

        section_title = (
            f"{number}. {title}"
        )

        self.page.insert_text(
            (
                MARGIN_LEFT,
                self.y,
            ),
            pdf_safe_text(
                section_title
            ),
            fontname="hebo",
            fontsize=12.5,
            color=BLACK,
        )

        self.y += 21

    def add_paragraph(
        self,
        text: str,
        *,
        font_size: float = 9.5,
        bold: bool = False,
        color=BLACK,
        space_after: float = 10,
    ) -> None:
        font_name = (
            "hebo"
            if bold
            else "helv"
        )

        lines = wrap_text(
            text,
            self.content_width,
            font_name,
            font_size,
        )

        line_height = (
            font_size * 1.5
        )

        required_height = (
            max(
                1,
                len(lines),
            )
            * line_height
            + space_after
        )

        self.ensure_space(
            required_height
        )

        assert self.page is not None

        for line in lines:
            self.page.insert_text(
                (
                    MARGIN_LEFT,
                    self.y,
                ),
                line,
                fontname=font_name,
                fontsize=font_size,
                color=color,
            )

            self.y += line_height

        self.y += space_after

    def add_table(
        self,
        rows: list[
            tuple[str, str]
        ],
    ) -> None:
        if not rows:
            return

        first_column_width = 185
        second_column_width = (
            self.content_width
            - first_column_width
        )

        for label, value in rows:
            label_lines = wrap_text(
                label,
                first_column_width - 18,
                "helv",
                9,
            )

            value_lines = wrap_text(
                value,
                second_column_width - 18,
                "helv",
                9,
            )

            line_count = max(
                len(label_lines),
                len(value_lines),
                1,
            )

            row_height = max(
                26,
                line_count * 13 + 10,
            )

            self.ensure_space(
                row_height
            )

            assert self.page is not None

            top = self.y - 10
            bottom = (
                top + row_height
            )

            self.page.draw_rect(
                pymupdf.Rect(
                    MARGIN_LEFT,
                    top,
                    MARGIN_LEFT
                    + first_column_width,
                    bottom,
                ),
                color=MEDIUM_GRAY,
                width=0.6,
            )

            self.page.draw_rect(
                pymupdf.Rect(
                    MARGIN_LEFT
                    + first_column_width,
                    top,
                    PAGE_WIDTH
                    - MARGIN_RIGHT,
                    bottom,
                ),
                color=MEDIUM_GRAY,
                width=0.6,
            )

            label_y = self.y + 2

            for line in label_lines:
                self.page.insert_text(
                    (
                        MARGIN_LEFT + 10,
                        label_y,
                    ),
                    line,
                    fontname="helv",
                    fontsize=9,
                    color=BLACK,
                )

                label_y += 13

            value_y = self.y + 2

            for line in value_lines:
                self.page.insert_text(
                    (
                        MARGIN_LEFT
                        + first_column_width
                        + 10,
                        value_y,
                    ),
                    line,
                    fontname="helv",
                    fontsize=9,
                    color=BLACK,
                )

                value_y += 13

            self.y = bottom + 10

        self.y += 8

    def add_piece(
        self,
        label: str,
        *,
        filenames: list[str] | None = None,
        bold: bool = False,
    ) -> None:
        font_name = (
            "hebo"
            if bold
            else "helv"
        )

        prefix = "- "

        lines = wrap_text(
            prefix + label,
            self.content_width,
            font_name,
            9.5,
        )

        filename_lines: list[str] = []

        if filenames:
            filename_text = (
                "Document : "
                + ", ".join(
                    filenames
                )
            )

            filename_lines = wrap_text(
                filename_text,
                self.content_width - 15,
                "helv",
                8,
            )

        required_height = (
            len(lines) * 14
            + len(filename_lines) * 11
            + 7
        )

        self.ensure_space(
            required_height
        )

        assert self.page is not None

        for line in lines:
            self.page.insert_text(
                (
                    MARGIN_LEFT,
                    self.y,
                ),
                line,
                fontname=font_name,
                fontsize=9.5,
                color=BLACK,
            )

            self.y += 14

        for line in filename_lines:
            self.page.insert_text(
                (
                    MARGIN_LEFT + 15,
                    self.y,
                ),
                line,
                fontname="helv",
                fontsize=8,
                color=DARK_GRAY,
            )

            self.y += 11

        self.y += 5


def build_project_description(
    profile,
) -> str | None:
    project_name = optional_value(
        attr(
            profile,
            "project_name",
        )
    )

    sector = optional_value(
        attr(
            profile,
            "sector",
        )
    )

    region = optional_value(
        attr(
            profile,
            "region",
        )
    )

    province = optional_value(
        attr(
            profile,
            "province",
        )
    )

    commune = optional_value(
        attr(
            profile,
            "commune",
        )
    )

    amount = format_amount(
        attr(
            profile,
            "investment_amount_mad",
        )
    )

    jobs_value = attr(
        profile,
        "planned_jobs",
        None,
    )

    sentences: list[str] = []

    if project_name and sector:
        sentences.append(
            (
                f"Le projet « {project_name} » "
                f"relève du secteur {sector}."
            )
        )

    elif project_name:
        sentences.append(
            f"Le projet est intitulé « {project_name} »."
        )

    elif sector:
        sentences.append(
            (
                "Le projet déclaré relève "
                f"du secteur {sector}."
            )
        )

    location_parts = [
        part
        for part in (
            commune,
            province,
            region,
        )
        if part
    ]

    if location_parts:
        sentences.append(
            (
                "Son implantation est prévue à "
                + ", ".join(
                    location_parts
                )
                + "."
            )
        )

    financial_parts: list[str] = []

    if amount:
        financial_parts.append(
            f"un investissement de {amount}"
        )

    if (
        jobs_value is not None
        and str(jobs_value).strip()
    ):
        financial_parts.append(
            (
                f"{jobs_value} emploi"
                + (
                    "s"
                    if int(jobs_value) != 1
                    else ""
                )
                + " prévu"
                + (
                    "s"
                    if int(jobs_value) != 1
                    else ""
                )
            )
        )

    if financial_parts:
        sentences.append(
            (
                "Les données confirmées indiquent "
                + " et ".join(
                    financial_parts
                )
                + "."
            )
        )

    if not sentences:
        return None

    return " ".join(
        sentences
    )


def build_investment_dossier_report(
    raw_payload: dict,
) -> tuple[bytes, str]:
    response = validate_report_payload(
        raw_payload
    )

    audit = response.audit
    profile = audit.project_profile
    results = audit.results
    summary = attr(
        audit,
        "summary",
        None,
    )

    project_name = (
        optional_value(
            attr(
                profile,
                "project_name",
            )
        )
        or "Projet d'investissement"
    )

    promoter_name = optional_value(
        attr(
            profile,
            "promoter_name",
        )
    )

    legal_form = optional_value(
        attr(
            profile,
            "legal_form",
        )
    )

    sector = optional_value(
        attr(
            profile,
            "sector",
        )
    )

    region = optional_value(
        attr(
            profile,
            "region",
        )
    )

    province = optional_value(
        attr(
            profile,
            "province",
        )
    )

    commune = optional_value(
        attr(
            profile,
            "commune",
        )
    )

    investment_amount = format_amount(
        attr(
            profile,
            "investment_amount_mad",
        )
    )

    planned_jobs = attr(
        profile,
        "planned_jobs",
        None,
    )

    investor_type_value = enum_value(
        attr(
            profile,
            "investor_type",
        )
    )

    land_status_value = enum_value(
        attr(
            profile,
            "land_status",
        )
    )

    work_values = [
        enum_value(work)
        for work in attr(
            profile,
            "works",
            [],
        )
    ]

    present_requirements = []

    missing_required_requirements = []
    missing_conditional_requirements = []
    recommended_absent_requirements = []

    for item in results:
        status = enum_value(
            attr(
                item,
                "status",
            )
        )

        requirement = attr(
            item,
            "requirement",
            None,
        )

        if requirement is None:
            continue

        level = enum_value(
            attr(
                requirement,
                "level",
            )
        )

        label = optional_value(
            attr(
                requirement,
                "label",
            )
        )

        if not label:
            continue

        requirement_item = {
            "label": label,
            "level": level,
            "required": (
                level
                in REQUIRED_LEVELS
            ),
            "filenames": [
                str(filename)
                for filename in attr(
                    item,
                    "submitted_files",
                    [],
                )
                if str(
                    filename
                ).strip()
            ],
        }

        if status in PRESENT_STATUSES:
            present_requirements.append(
                requirement_item
            )

        elif status in MISSING_STATUSES:
            if level in REQUIRED_LEVELS:
                missing_required_requirements.append(
                    requirement_item
                )

            elif level in CONDITIONAL_LEVELS:
                missing_conditional_requirements.append(
                    requirement_item
                )

        elif (
            status
            in RECOMMENDED_ABSENT_STATUSES
        ):
            recommended_absent_requirements.append(
                requirement_item
            )

    document = pymupdf.open()

    writer = ProfessionalPdfWriter(
        document
    )

    generated_at = datetime.now(
        timezone.utc
    ).astimezone()

    subtitle_parts = []

    if region:
        subtitle_parts.append(
            f"Région {region}"
        )

    subtitle_parts.append(
        (
            "Édité le "
            + generated_at.strftime(
                "%d/%m/%Y"
            )
        )
    )

    writer.add_document_header(
        title=project_name,
        subtitle=" - ".join(
            subtitle_parts
        ),
    )

    section_number = 1

    identity_document_number = str(
        attr(
            profile,
            "identity_document_number",
            "",
        )
        or ""
    ).strip()

    identification_rows = []

    if promoter_name:
        identification_rows.append(
            (
                (
                    "Raison sociale"
                    if legal_form
                    else "Porteur du projet"
                ),
                promoter_name,
            )
        )

    if identity_document_number:
        identification_rows.append(
            (
                "CIN / Passeport",
                identity_document_number,
            )
        )

    if legal_form:
        identification_rows.append(
            (
                "Forme juridique",
                legal_form,
            )
        )

    if sector:
        identification_rows.append(
            (
                "Secteur d'activité",
                sector,
            )
        )

    if region:
        identification_rows.append(
            (
                "Région d'implantation",
                region,
            )
        )

    if province:
        identification_rows.append(
            (
                "Province",
                province,
            )
        )

    if commune:
        identification_rows.append(
            (
                "Commune",
                commune,
            )
        )

    if investment_amount:
        identification_rows.append(
            (
                "Montant d'investissement",
                investment_amount,
            )
        )

    if planned_jobs is not None:
        identification_rows.append(
            (
                "Emplois prévus",
                str(planned_jobs),
            )
        )

    if identification_rows:
        writer.add_section_title(
            section_number,
            "Identification du porteur de projet",
        )

        writer.add_table(
            identification_rows
        )

        section_number += 1

    project_description = (
        build_project_description(
            profile
        )
    )

    if project_description:
        writer.add_section_title(
            section_number,
            "Présentation du projet",
        )

        writer.add_paragraph(
            project_description,
        )

        section_number += 1

    project_rows = []

    if investor_type_value:
        project_rows.append(
            (
                "Type d'investisseur",
                INVESTOR_LABELS.get(
                    investor_type_value,
                    investor_type_value,
                ),
            )
        )

    if land_status_value:
        project_rows.append(
            (
                "Situation foncière",
                LAND_LABELS.get(
                    land_status_value,
                    land_status_value,
                ),
            )
        )

    if work_values:
        project_rows.append(
            (
                "Nature des travaux",
                ", ".join(
                    WORK_LABELS.get(
                        work,
                        work,
                    )
                    for work
                    in work_values
                ),
            )
        )

    if attr(
        profile,
        "requests_incentives",
        False,
    ):
        project_rows.append(
            (
                "Aide à l'investissement",
                "Demandée",
            )
        )

    if attr(
        profile,
        "requests_bank_financing",
        False,
    ):
        project_rows.append(
            (
                "Financement bancaire",
                "Demandé",
            )
        )

    if attr(
        profile,
        "potential_environmental_impact",
        False,
    ):
        project_rows.append(
            (
                "Volet environnemental",
                (
                    "À prendre en compte "
                    "dans le dossier"
                ),
            )
        )

    if attr(
        profile,
        "regulated_activity",
        False,
    ):
        project_rows.append(
            (
                "Activité réglementée",
                (
                    "Autorisation sectorielle "
                    "à prévoir"
                ),
            )
        )

    if project_rows:
        writer.add_section_title(
            section_number,
            "Éléments du projet",
        )

        writer.add_table(
            project_rows
        )

        section_number += 1

    if present_requirements:
        writer.add_section_title(
            section_number,
            "Pièces jointes au dossier",
        )

        for requirement in (
            present_requirements
        ):
            writer.add_piece(
                requirement["label"],
                filenames=(
                    requirement[
                        "filenames"
                    ]
                ),
                bold=(
                    requirement[
                        "required"
                    ]
                ),
            )

        section_number += 1

    missing_requirements = (
        missing_required_requirements
        + missing_conditional_requirements
    )

    if missing_requirements:
        writer.add_section_title(
            section_number,
            (
                "Pièces obligatoires ou "
                "conditionnelles manquantes"
            ),
        )

        for requirement in missing_requirements:
            level = requirement["level"]

            if level in REQUIRED_LEVELS:
                level_label = "Obligatoire"

            else:
                level_label = "Conditionnelle"

            writer.add_piece(
                (
                    requirement["label"]
                    + " ("
                    + level_label
                    + ")"
                ),
                bold=(
                    level
                    in REQUIRED_LEVELS
                ),
            )

        section_number += 1

    if recommended_absent_requirements:
        writer.add_section_title(
            section_number,
            "Pièces recommandées absentes",
        )

        for requirement in (
            recommended_absent_requirements
        ):
            writer.add_piece(
                (
                    requirement["label"]
                    + " (Recommandée)"
                ),
            )

        section_number += 1

    writer.ensure_space(48)

    writer.add_paragraph(
        (
            "Ce document constitue une synthèse "
            "du dossier. La validation administrative "
            "finale relève des services compétents."
        ),
        font_size=8,
        color=DARK_GRAY,
        space_after=2,
    )

    page_count = len(
        document
    )

    for page_index, page in enumerate(
        document
    ):
        page.draw_line(
            (
                MARGIN_LEFT,
                PAGE_HEIGHT - 31,
            ),
            (
                PAGE_WIDTH
                - MARGIN_RIGHT,
                PAGE_HEIGHT - 31,
            ),
            color=LIGHT_GRAY,
            width=0.5,
        )

        page.insert_text(
            (
                MARGIN_LEFT,
                PAGE_HEIGHT - 18,
            ),
            pdf_safe_text(
                "Dossier de projet"
            ),
            fontname="helv",
            fontsize=7.5,
            color=MEDIUM_GRAY,
        )

        page.insert_text(
            (
                PAGE_WIDTH - 93,
                PAGE_HEIGHT - 18,
            ),
            pdf_safe_text(
                (
                    f"Page {page_index + 1}"
                    f"/{page_count}"
                )
            ),
            fontname="helv",
            fontsize=7.5,
            color=MEDIUM_GRAY,
        )

    document.set_metadata(
        {
            "title": (
                "Synthèse du dossier "
                "d'investissement"
            ),
            "author": (
                "CRI Guelmim-Oued Noun"
            ),
            "subject": (
                "Dossier de projet"
            ),
        }
    )

    pdf_content = document.tobytes(
        garbage=4,
        deflate=True,
    )

    document.close()

    filename = (
        "dossier_projet_"
        + sanitize_filename(
            project_name
        )
        + ".pdf"
    )

    return (
        pdf_content,
        filename,
    )
