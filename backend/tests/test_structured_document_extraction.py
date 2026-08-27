from app.structured_document_extraction import (
    extract_structured_fields,
    parse_amount_mad,
)


def test_extracts_fields_without_colons():
    text = """
Nom du projet Unité industrielle Sud
Raison sociale h
CIN / Passeport JZ 9104
Forme juridique SARL
Secteur d'activité Industrie
Région d'implantation Guelmim-Oued Noun
Province Assa-Zag
Commune Assa
Montant d'investissement 500 000 DH
Emplois prévus 25
Type d'investisseur Société en création
Situation foncière Non identifié
Nature des travaux aucuns_travaux
"""

    result = extract_structured_fields(text)

    assert result["project_name"] == (
        "Unité industrielle Sud"
    )
    assert result["promoter_name"] == "h"
    assert result[
        "identity_document_number"
    ] == "JZ 9104"
    assert result["legal_form"] == "SARL"
    assert result["sector"] == "Industrie"
    assert result["region"] == (
        "Guelmim-Oued Noun"
    )
    assert result["province"] == "Assa-Zag"
    assert result["commune"] == "Assa"
    assert result[
        "investment_amount_mad"
    ] == 500000
    assert result["planned_jobs"] == 25
    assert result["investor_type"] == (
        "societe_en_creation"
    )
    assert result["land_status"] == (
        "non_identifie"
    )
    assert result["works"] == [
        "aucuns_travaux"
    ]


def test_extracts_colon_and_dash_variants():
    text = """
Nom du projet : Station solaire
Promoteur - Atlas Invest
Forme juridique : SA
Secteur : Énergie renouvelable
Province : Tan-Tan
Commune - El Ouatia
Investissement total : 2,5 MDH
Nombre d'emplois : 40
Situation foncière : Propriétaire
Nature des travaux : Construction
"""

    result = extract_structured_fields(text)

    assert result["project_name"] == (
        "Station solaire"
    )
    assert result["promoter_name"] == (
        "Atlas Invest"
    )
    assert result["sector"] == (
        "Énergie renouvelable"
    )
    assert result["province"] == "Tan-Tan"
    assert result["commune"] == "El Ouatia"

    assert result[
        "investment_amount_mad"
    ] == 2_500_000

    assert result["planned_jobs"] == 40
    assert result["land_status"] == (
        "proprietaire"
    )
    assert result["works"] == [
        "construction"
    ]


def test_explicit_sector_is_not_replaced_by_prose():
    text = """
Secteur d'activité Industrie
Le dossier sera étudié par les services compétents.
Une activité agroalimentaire existe également
dans la zone voisine.
"""

    result = extract_structured_fields(text)

    assert result["sector"] == "Industrie"


def test_province_and_commune_are_independent():
    text = """
Région Guelmim-Oued Noun
Province Guelmim
Commune Bouizakarne
"""

    result = extract_structured_fields(text)

    assert result["province"] == "Guelmim"
    assert result["commune"] == "Bouizakarne"


def test_same_name_can_be_province_and_commune():
    text = """
Province Guelmim
Commune Guelmim
"""

    result = extract_structured_fields(text)

    assert result["province"] == "Guelmim"
    assert result["commune"] == "Guelmim"


def test_amount_variants():
    assert parse_amount_mad(
        "500 000 DH"
    ) == 500000

    assert parse_amount_mad(
        "5.000.000 MAD"
    ) == 5000000

    assert parse_amount_mad(
        "2,5 MDH"
    ) == 2500000

def test_specific_location_label_has_priority():
    text = """
Region Region-Nord - Edite le 01/01/2026
Region d'implantation Region-Sud
"""

    result = extract_structured_fields(text)

    assert result["region"] == "Region-Sud"



def test_handles_split_label_words():
    text = """
Secteur d' activite Industrie textile
Region d implantation Guelmim-Oued Noun
"""

    result = extract_structured_fields(text)

    assert result["sector"] == "Industrie textile"
    assert result["region"] == "Guelmim-Oued Noun"


def test_extracts_values_from_next_line():
    text = """
Raison sociale
ATLAS INVEST SUD SARL
Secteur d'activite
Agroalimentaire
Region d'implantation
Guelmim-Oued Noun (categorie A)
Montant d'investissement
20 000 000 DH
Emplois prevus
45 postes permanents
"""

    result = extract_structured_fields(text)

    assert result["promoter_name"] == (
        "ATLAS INVEST SUD SARL"
    )
    assert result["sector"] == (
        "Agroalimentaire"
    )
    assert result["region"] == (
        "Guelmim-Oued Noun"
    )
    assert result[
        "investment_amount_mad"
    ] == 20_000_000
    assert result["planned_jobs"] == 45


def test_missing_value_does_not_consume_next_label():
    text = """
Raison sociale
Secteur d'activite
Industrie
"""

    result = extract_structured_fields(text)

    assert "promoter_name" not in result
    assert result["sector"] == "Industrie"
