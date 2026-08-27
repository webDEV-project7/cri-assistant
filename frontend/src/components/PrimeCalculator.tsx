"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  getTpmeCatalog,
  simulateTpmePrimes,
  type TpmeCatalog,
  type TpmeSimulationRequest,
  type TpmeSimulationResponse,
} from "@/lib/api";


type TpmeFormState = {
  total_investment_mad: number;
  stable_jobs: number;
  equity_financing_mad: number;

  company_status: "" | "new" | "existing";
  annual_turnover_mad: number | null;

  province: string;
  sector: string;
  branch: string;
  priority_activity_name: string;

  studies_trademarks_processes_mad: number;
  private_land_mad: number;
  vehicles_mad: number;
  related_party_investment_mad: number;

  private_land_eligible: boolean;

  owned_over_25_by_large_company: boolean;
  has_public_entity_shareholder: boolean;
};


const initialForm: TpmeFormState = {
  total_investment_mad: 0,
  stable_jobs: 0,
  equity_financing_mad: 0,

  company_status: "",
  annual_turnover_mad: null,

  province: "Guelmim",
  sector: "",
  branch: "",
  priority_activity_name: "",

  studies_trademarks_processes_mad: 0,
  private_land_mad: 0,
  vehicles_mad: 0,
  related_party_investment_mad: 0,

  private_land_eligible: false,

  owned_over_25_by_large_company: false,
  has_public_entity_shareholder: false,
};


function formatMad(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }

  return new Intl.NumberFormat("fr-MA", {
    style: "currency",
    currency: "MAD",
    maximumFractionDigits: 0,
  }).format(value);
}


function formatRatio(value: number | null | undefined): string {
  if (value === null || value === undefined) {
    return "—";
  }

  return new Intl.NumberFormat("fr-MA", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(value);
}


const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "11px 14px",
  borderRadius: "10px",
  border: "1px solid #EDE2D4",
  fontSize: "14px",
  color: "#1C1610",
  background: "#FFFFFF",
  outline: "none",
  boxSizing: "border-box",
  fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
  transition: "border-color 0.15s ease, box-shadow 0.15s ease",
};


const labelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "6px",
};


const labelTextStyle: React.CSSProperties = {
  fontSize: "13.5px",
  fontWeight: 600,
  color: "#1C1610",
  fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
};


const hintStyle: React.CSSProperties = {
  fontSize: "11.5px",
  color: "#6B5E4E",
  marginTop: "3px",
  fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
};


const gridStyle: React.CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))",
  gap: "18px",
  marginBottom: "20px",
};


function SectionTitle({
  title,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "14px",
        margin: "28px 0 18px 0",
      }}
    >
      <h3
        style={{
          fontSize: "1.15rem",
          fontWeight: 700,
          color: "#1C1610",
          margin: 0,
          whiteSpace: "nowrap",
          fontFamily: "var(--font-fraunces), Georgia, serif",
        }}
      >
        {title}
      </h3>
      <div
        style={{
          flex: 1,
          height: "1px",
          background: "#EDE2D4",
        }}
      />
    </div>
  );
}


function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
  hint?: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "10px",
        padding: "12px 16px",
        borderRadius: "12px",
        background: "#ECE4D8",
        height: "100%",
        boxSizing: "border-box",
      }}
    >
      <span
        style={{
          fontSize: "13px",
          fontWeight: 600,
          color: "#2C2018",
          fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
          lineHeight: 1.2,
        }}
      >
        {label}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        style={{
          width: "42px",
          height: "22px",
          borderRadius: "9999px",
          background: checked ? "#6B1222" : "#D4C9B8",
          border: "none",
          cursor: "pointer",
          position: "relative",
          flexShrink: 0,
          transition: "background 0.2s",
        }}
      >
        <span
          style={{
            position: "absolute",
            top: "2px",
            left: checked ? "22px" : "2px",
            width: "18px",
            height: "18px",
            borderRadius: "50%",
            background: "#FFFFFF",
            boxShadow: "0 1px 3px rgba(0,0,0,0.2)",
            transition: "left 0.2s",
          }}
        />
      </button>
    </div>
  );
}


const eligibilityLabels: Record<string, string> = {
  investment_amount: "Montant d'investissement",
  employment_ratio: "Ratio d'emplois stables",
  equity_financing: "Financement par fonds propres",
  turnover_or_new_company: "Situation de l'entreprise / chiffre d'affaires",
  ownership: "Participation d'une grande entreprise",
  public_shareholder: "Participation d'une personne morale publique",
  eligible_activity: "Branche d’activité éligible",
};


export default function PrimeCalculator() {
  const [form, setForm] = useState<TpmeFormState>(initialForm);

  const [
    hasRestrictedParticipation,
    setHasRestrictedParticipation,
  ] = useState(false);

  const [catalog, setCatalog] =
    useState<TpmeCatalog | null>(null);

  const [catalogError, setCatalogError] =
    useState<string | null>(null);

  const [isCatalogLoading, setIsCatalogLoading] =
    useState(true);

  const [result, setResult] =
    useState<TpmeSimulationResponse | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [isCalculating, setIsCalculating] =
    useState(false);


  useEffect(() => {
    let active = true;

    async function loadCatalog() {
      setIsCatalogLoading(true);
      setCatalogError(null);

      try {
        const data = await getTpmeCatalog();

        if (active) {
          setCatalog(data);
        }
      } catch (requestError) {
        if (active) {
          setCatalogError(
            requestError instanceof Error
              ? requestError.message
              : "Impossible de charger le catalogue TPME."
          );
        }
      } finally {
        if (active) {
          setIsCatalogLoading(false);
        }
      }
    }

    void loadCatalog();

    return () => {
      active = false;
    };
  }, []);


  const selectedSector =
    catalog?.sectors.find(
      (sector) => sector.name === form.sector
    ) ?? null;


  const selectedBranch =
    selectedSector?.branches.find(
      (branch) => branch.name === form.branch
    ) ?? null;


  const selectedProvince =
    catalog?.provinces.find(
      (province) => province.name === form.province
    ) ?? null;


  const priorityActivities =
    selectedBranch?.priority_activities ?? [];
  const detailedExpenses =
    form.studies_trademarks_processes_mad +
    form.private_land_mad +
    form.vehicles_mad +
    form.related_party_investment_mad;


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError(null);
    setResult(null);

    /* PARTICIPATION_ELIGIBILITY_VALIDATION */
    if (
      hasRestrictedParticipation &&
      !form.owned_over_25_by_large_company &&
      !form.has_public_entity_shareholder
    ) {
      setError(
        "Précisez la situation de participation concernée."
      );
      return;
    }

    if (!catalog) {
      setError(
        "Le catalogue réglementaire TPME n'est pas disponible."
      );
      return;
    }

    if (!selectedSector) {
      setError("Veuillez sélectionner un secteur d'activité.");
      return;
    }

    if (!selectedBranch) {
      setError("Veuillez sélectionner une branche d'activité.");
      return;
    }

    if (
      form.equity_financing_mad >
      form.total_investment_mad
    ) {
      setError(
        "Les fonds propres ne peuvent pas dépasser l'investissement total."
      );
      return;
    }

    if (
      detailedExpenses >
      form.total_investment_mad
    ) {
      setError(
        "La somme des composantes détaillées ne peut pas dépasser l'investissement total."
      );
      return;
    }

    if (!form.company_status) {
      setError(
        "Veuillez sélectionner la situation de l'entreprise."
      );
      return;
    }

    if (
      form.company_status === "existing" &&
      form.annual_turnover_mad === null
    ) {
      setError(
        "Veuillez renseigner le chiffre d'affaires de l'entreprise."
      );
      return;
    }

    const payload: TpmeSimulationRequest = {
      total_investment_mad:
        form.total_investment_mad,

      stable_jobs:
        form.stable_jobs,

      equity_financing_mad:
        form.equity_financing_mad,

      company_age_years:
        form.company_status === "new" ? 0 : 3,

      annual_turnover_mad:
        form.company_status === "existing"
          ? form.annual_turnover_mad
          : null,

      studies_trademarks_processes_mad:
        form.studies_trademarks_processes_mad,

      private_land_mad:
        form.private_land_mad,

      vehicles_mad:
        form.vehicles_mad,

      related_party_investment_mad:
        form.related_party_investment_mad,

      private_land_eligible:
        form.private_land_mad > 0
          ? form.private_land_eligible
          : false,

      owned_over_25_by_large_company:
        form.owned_over_25_by_large_company,

      has_public_entity_shareholder:
        form.has_public_entity_shareholder,

      activity_eligible:
        true,

      tourism_activity:
        selectedSector.tourism_activity,

      priority_activity:
        form.priority_activity_name.length > 0,

      territorial_category:
        selectedProvince?.territorial_category ?? null,
    };

    setIsCalculating(true);

    try {
      const response =
        await simulateTpmePrimes(payload);

      setResult(response);
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Une erreur est survenue pendant le calcul."
      );
    } finally {
      setIsCalculating(false);
    }
  }


  function resetCalculator() {
    setForm(initialForm);
    setHasRestrictedParticipation(false);
    setResult(null);
    setError(null);
  }


  const failedEligibility =
    result
      ? Object.entries(
          result.eligibility_details
        ).filter(([, valid]) => !valid)
      : [];

  // Count incomplete required sections
  const incompleteSections = [
    !form.total_investment_mad || !form.stable_jobs || !form.equity_financing_mad,
    !form.company_status,
    !form.sector || !form.branch,
  ].filter(Boolean).length;


  return (
    <div data-prime-modern="true"
      style={{
        minHeight: "calc(100vh - 72px)",
        background: "#F5F0E8",
        fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div
        style={{
          padding: "45px 32px 52px",
          color: "#000",
        }}
      >
        <div
          style={{
            maxWidth: "1000px",
            margin: "0 auto",
          }}
        >
          <nav
            style={{
              marginBottom: "20px",
            }}
          >
            <span
              style={{
                fontSize: "13px",
                color: "#555",
              }}
            >
              Espace investisseur{" "}
              <span style={{ margin: "0 6px" }}>
                /
              </span>
              <span
                style={{
                  color: "#000",
                  fontWeight: 600,
                }}
              >
                Primes d’investissement
              </span>
            </span>
          </nav>

          <h1
            style={{
              fontFamily:
                "var(--font-outfit), var(--font-inter), sans-serif",
              fontSize: "clamp(26px,4vw,40px)",
              fontWeight: 700,
              margin: "0 0 14px 0",
              lineHeight: 1.15,
            }}
          >
            Calculateur des primes d’investissement
          </h1>

          <p
            style={{
              fontSize: "15.5px",
              color: "#333",
              margin: "0 0 4px 0",
            }}
          >
            Simulez les primes applicables à votre
            projet dans le cadre du dispositif TPME.
          </p>

          <p
            style={{
              fontSize: "14px",
              color: "#000",
              margin: 0,
              fontWeight: 600,
            }}
          >
            Le montant d’investissement primable est
            déterminé automatiquement.
          </p>
        </div>
      </div>


      <div
        style={{
          flex: 1,
          padding: "0 32px 32px",
          overflowY: "auto",
        }}
      >
        <form id="prime-form" onSubmit={handleSubmit}>
          <div
            style={{
              background: "transparent",
            }}
          >


            <div style={{ padding: "16px 24px" }}>
              <SectionTitle title="Informations du projet" />

              <div style={gridStyle}>
                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Investissement total (MAD) <span style={{ color: "#8B0000" }}>*</span>
                  </span>
                  <input
                    style={inputStyle}
                    type="number"
                    min="1000000"
                    max="49999999.99"
                    step="1000"
                    required
                    placeholder="Min. 1 000 000 MAD"
                    value={form.total_investment_mad || ""}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        total_investment_mad: Number(event.target.value),
                      }))
                    }
                  />
                </label>

                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Nombre d’emplois stables <span style={{ color: "#8B0000" }}>*</span>
                  </span>
                  <input
                    style={inputStyle}
                    type="number"
                    min="0"
                    step="1"
                    required
                    placeholder="0"
                    value={form.stable_jobs || ""}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        stable_jobs: Number(event.target.value),
                      }))
                    }
                  />
                </label>

                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Fonds propres (MAD) <span style={{ color: "#8B0000" }}>*</span>
                  </span>
                  <input
                    style={inputStyle}
                    type="number"
                    min="0"
                    step="1000"
                    required
                    placeholder="Minimum 10 %"
                    value={form.equity_financing_mad || ""}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        equity_financing_mad: Number(event.target.value),
                      }))
                    }
                  />
                </label>

                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Secteur <span style={{ color: "#8B0000" }}>*</span>
                  </span>
                  <select
                    style={inputStyle}
                    required
                    disabled={isCatalogLoading || !catalog}
                    value={form.sector}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        sector: event.target.value,
                        branch: "",
                        priority_activity_name: "",
                      }))
                    }
                  >
                    <option value="">
                      {isCatalogLoading ? "Chargement..." : "Sélectionner..."}
                    </option>
                    {(catalog?.sectors ?? []).map((sector) => (
                      <option key={sector.name} value={sector.name}>
                        {sector.name}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <SectionTitle title="Situation de l’entreprise" />

              <div style={gridStyle}>
                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "12px 16px",
                    borderRadius: "12px",
                    border: form.company_status === "new" ? "1.5px solid #6B1222" : "1px solid #E2D8CC",
                    background: "#FFFFFF",
                    cursor: "pointer",
                    boxSizing: "border-box",
                  }}
                >
                  <input
                    type="radio"
                    name="company_status"
                    value="new"
                    required
                    checked={form.company_status === "new"}
                    onChange={() =>
                      setForm((current) => ({
                        ...current,
                        company_status: "new",
                        annual_turnover_mad: null,
                      }))
                    }
                    style={{
                      width: "16px",
                      height: "16px",
                      accentColor: "#6B1222",
                    }}
                  />
                  <div>
                    <div style={{ fontSize: "13.5px", fontWeight: 700, color: "#1A1A1A", fontFamily: "var(--font-outfit), var(--font-inter), sans-serif" }}>
                      Nouvellement créée
                    </div>
                    <div style={{ fontSize: "11px", color: "#8A7968", fontFamily: "var(--font-outfit), var(--font-inter), sans-serif" }}>
                      Moins de 3 ans
                    </div>
                  </div>
                </label>

                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "12px 16px",
                    borderRadius: "12px",
                    border: form.company_status === "existing" ? "1.5px solid #6B1222" : "1px solid #E2D8CC",
                    background: "#FFFFFF",
                    cursor: "pointer",
                    boxSizing: "border-box",
                  }}
                >
                  <input
                    type="radio"
                    name="company_status"
                    value="existing"
                    required
                    checked={form.company_status === "existing"}
                    onChange={() =>
                      setForm((current) => ({
                        ...current,
                        company_status: "existing",
                      }))
                    }
                    style={{
                      width: "16px",
                      height: "16px",
                      accentColor: "#6B1222",
                    }}
                  />
                  <div>
                    <div style={{ fontSize: "13.5px", fontWeight: 700, color: "#1A1A1A", fontFamily: "var(--font-outfit), var(--font-inter), sans-serif" }}>
                      Entreprise existante
                    </div>
                    <div style={{ fontSize: "11px", color: "#8A7968", fontFamily: "var(--font-outfit), var(--font-inter), sans-serif" }}>
                      3 ans ou plus
                    </div>
                  </div>
                </label>

                
                <div
                  className="prime-participation-question"
                  style={{ gridColumn: "1 / -1" }}
                >
                  <div className="prime-participation-copy">
                    <strong>
                      L’entreprise présente-t-elle l’une de ces situations ?
                    </strong>

                    <span>
                      Participation supérieure à 25 % détenue par une
                      grande entreprise ou présence d’une personne morale
                      de droit public parmi les associés/actionnaires.
                    </span>
                  </div>

                  <div
                    className="prime-participation-answer"
                    role="radiogroup"
                    aria-label="Situation de participation"
                  >
                    <label
                      className={
                        !hasRestrictedParticipation
                          ? "is-selected"
                          : ""
                      }
                    >
                      <input
                        type="radio"
                        name="restricted-participation"
                        checked={!hasRestrictedParticipation}
                        onChange={() => {
                          setHasRestrictedParticipation(false);

                          setForm((current) => ({
                            ...current,
                            owned_over_25_by_large_company: false,
                            has_public_entity_shareholder: false,
                          }));
                        }}
                      />

                      <span>Non</span>
                    </label>

                    <label
                      className={
                        hasRestrictedParticipation
                          ? "is-selected"
                          : ""
                      }
                    >
                      <input
                        type="radio"
                        name="restricted-participation"
                        checked={hasRestrictedParticipation}
                        onChange={() => {
                          setHasRestrictedParticipation(true);
                        }}
                      />

                      <span>Oui</span>
                    </label>
                  </div>
                </div>

                {hasRestrictedParticipation && (
                  <div
                    className="prime-participation-details"
                    style={{ gridColumn: "1 / -1" }}
                  >
                    <div className="prime-participation-details-title">
                      Précisez la situation concernée
                    </div>

                    <Toggle
                      checked={form.owned_over_25_by_large_company}
                      onChange={(value) =>
                        setForm((current) => ({
                          ...current,
                          owned_over_25_by_large_company: value,
                        }))
                      }
                      label="Participation > 25 % grande entreprise"
                    />

                    <Toggle
                      checked={form.has_public_entity_shareholder}
                      onChange={(value) =>
                        setForm((current) => ({
                          ...current,
                          has_public_entity_shareholder: value,
                        }))
                      }
                      label="Participation publique"
                    />
                  </div>
                )}
              </div>

              {form.company_status === "existing" && (
                <div style={gridStyle}>
                  <label style={labelStyle}>
                    <span style={labelTextStyle}>
                      Chiffre d’affaires annuel HT (MAD) <span style={{ color: "#8B0000" }}>*</span>
                    </span>
                    <input
                      style={inputStyle}
                      type="number"
                      min="1000000"
                      max="199999999.99"
                      step="1000"
                      required
                      placeholder="Ex. 10 000 000"
                      value={form.annual_turnover_mad ?? ""}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          annual_turnover_mad:
                            event.target.value === ""
                              ? null
                              : Number(event.target.value),
                        }))
                      }
                    />
                  </label>
                </div>
              )}

              <SectionTitle title="Localisation et activité" />

              <div style={gridStyle}>
                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Région
                  </span>

                  <select
                    style={{
                      ...inputStyle,
                      background: "#F8FAFC",
                    }}
                    disabled
                  >
                    <option>
                      {catalog?.region ??
                        "Guelmim-Oued Noun"}
                    </option>
                  </select>
                </label>


                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Province / Préfecture{" "}
                    <span style={{ color: "#EF4444" }}>
                      *
                    </span>
                  </span>

                  <select
                    style={inputStyle}
                    required
                    value={form.province}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        province: event.target.value,
                      }))
                    }
                  >
                    {(catalog?.provinces ?? []).map(
                      (province) => (
                        <option
                          key={province.name}
                          value={province.name}
                        >
                          {province.name}
                        </option>
                      )
                    )}
                  </select>

                  {selectedProvince && (
                    <span style={hintStyle}>
                      Catégorie territoriale :{" "}
                      {selectedProvince.territorial_category}
                    </span>
                  )}
                </label>


                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Secteur{" "}
                    <span style={{ color: "#EF4444" }}>
                      *
                    </span>
                  </span>

                  <select
                    style={inputStyle}
                    required
                    disabled={
                      isCatalogLoading || !catalog
                    }
                    value={form.sector}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        sector: event.target.value,
                        branch: "",
                        priority_activity_name: "",
                      }))
                    }
                  >
                    <option value="">
                      {isCatalogLoading
                        ? "Chargement..."
                        : "Sélectionner..."}
                    </option>

                    {(catalog?.sectors ?? []).map(
                      (sector) => (
                        <option
                          key={sector.name}
                          value={sector.name}
                        >
                          {sector.name}
                        </option>
                      )
                    )}
                  </select>
                </label>


                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Branche d’activité{" "}
                    <span style={{ color: "#EF4444" }}>
                      *
                    </span>
                  </span>

                  <select
                    style={inputStyle}
                    required
                    disabled={!selectedSector}
                    value={form.branch}
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        branch: event.target.value,
                        priority_activity_name: "",
                      }))
                    }
                  >
                    <option value="">
                      Sélectionner...
                    </option>

                    {(selectedSector?.branches ?? []).map(
                      (branch) => (
                        <option
                          key={branch.name}
                          value={branch.name}
                        >
                          {branch.name}
                        </option>
                      )
                    )}
                  </select>
                </label>


                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Activité prioritaire
                  </span>

                  <select
                    style={inputStyle}
                    disabled={
                      !selectedBranch ||
                      priorityActivities.length === 0
                    }
                    value={
                      form.priority_activity_name
                    }
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        priority_activity_name:
                          event.target.value,
                      }))
                    }
                  >
                    <option value="">
                      {selectedBranch &&
                      priorityActivities.length === 0
                        ? "Aucune activité prioritaire"
                        : "Non concerné / sélectionner..."}
                    </option>

                    {priorityActivities.map(
                      (activity) => (
                        <option
                          key={activity}
                          value={activity}
                        >
                          {activity}
                        </option>
                      )
                    )}
                  </select>

                  {form.priority_activity_name && (
                    <span
                      style={{
                        ...hintStyle,
                        color: "#059669",
                      }}
                    >
                      Activité prioritaire sélectionnée.
                    </span>
                  )}
                </label>
              </div>


              <SectionTitle
                title="Composition de l'investissement"
                description="Ces montants permettent au système de déterminer automatiquement la base primable."
              />

              <div style={gridStyle}>
                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Études, marques et procédés (MAD)
                  </span>

                  <input
                    style={inputStyle}
                    type="number"
                    min="0"
                    step="1000"
                    placeholder="0"
                    value={
                      form
                        .studies_trademarks_processes_mad ||
                      ""
                    }
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        studies_trademarks_processes_mad:
                          Number(event.target.value),
                      }))
                    }
                  />
                </label>


                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Foncier privé (MAD)
                  </span>

                  <input
                    style={inputStyle}
                    type="number"
                    min="0"
                    step="1000"
                    placeholder="0"
                    value={
                      form.private_land_mad || ""
                    }
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        private_land_mad:
                          Number(event.target.value),
                      }))
                    }
                  />
                </label>


                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Véhicules (MAD)
                  </span>

                  <input
                    style={inputStyle}
                    type="number"
                    min="0"
                    step="1000"
                    placeholder="0"
                    value={
                      form.vehicles_mad || ""
                    }
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        vehicles_mad:
                          Number(event.target.value),
                      }))
                    }
                  />

                  <span style={hintStyle}>
                    Cette dépense sera exclue automatiquement
                    de la base primable.
                  </span>
                </label>


                <label style={labelStyle}>
                  <span style={labelTextStyle}>
                    Dépenses entre entreprises liées (MAD)
                  </span>

                  <input
                    style={inputStyle}
                    type="number"
                    min="0"
                    step="1000"
                    placeholder="0"
                    value={
                      form
                        .related_party_investment_mad ||
                      ""
                    }
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        related_party_investment_mad:
                          Number(event.target.value),
                      }))
                    }
                  />

                  <span style={hintStyle}>
                    Dépenses réalisées entre entreprises
                    détenues par un même investisseur.
                  </span>
                </label>
              </div>


              {form.private_land_mad > 0 && (
                <div
                  style={{
                    padding: "16px 18px",
                    borderRadius: "12px",
                    background: "#F8FAFC",
                    marginBottom: "20px",
                  }}
                >
                  <Toggle
                    checked={
                      form.private_land_eligible
                    }
                    onChange={(value) =>
                      setForm((current) => ({
                        ...current,
                        private_land_eligible: value,
                      }))
                    }
                    label="Le foncier privé concerne une activité ouvrant droit à sa prise en compte"
                    hint="Projet industriel, touristique, d'animation touristique ou artisanal."
                  />
                </div>
              )}


              <div
                style={{
                  fontSize: "12px",
                  color:
                    detailedExpenses >
                    form.total_investment_mad
                      ? "#DC2626"
                      : "#64748B",
                  marginBottom: "6px",
                }}
              >
                Composantes détaillées :{" "}
                <strong>
                  {formatMad(detailedExpenses)}
                </strong>
              </div>
            </div>


            {(error || catalogError) && (
              <div
                role="alert"
                style={{
                  margin: "0 0 16px",
                  padding: "10px 14px",
                  borderRadius: "6px",
                  background: "#FEF2F2",
                  border: "1px solid #FECACA",
                  color: "#DC2626",
                  fontSize: "13px",
                  fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
                }}
              >
                {error || catalogError}
              </div>
            )}
          </div>
        </form>

        {/* Sticky bottom action bar */}
        <div
          style={{
            position: "sticky",
            bottom: 0,
            background: "#FAF8F4",
            borderTop: "1px solid #D4C9B8",
            padding: "14px 32px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            zIndex: 10,
          }}
        >
          <span
            style={{
              fontSize: "13px",
              color: incompleteSections > 0 ? "#8B6914" : "#059669",
              fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
            }}
          >
            {incompleteSections > 0
              ? `● ${incompleteSections} section${incompleteSections > 1 ? "s" : ""} à compléter`
              : "● Formulaire complet"}
          </span>

          <div style={{ display: "flex", gap: "12px" }}>
            <button
              type="button"
              onClick={resetCalculator}
              style={{
                padding: "10px 22px",
                borderRadius: "9999px",
                border: "1.5px solid #8B0000",
                background: "#FFFFFF",
                color: "#8B0000",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
              }}
            >
              Réinitialiser
            </button>

            <button
              type="submit"
              form="prime-form"
              disabled={isCalculating || isCatalogLoading || !catalog}
              style={{
                padding: "10px 28px",
                borderRadius: "9999px",
                border: "none",
                background:
                  isCalculating || isCatalogLoading || !catalog
                    ? "#C8A8A8"
                    : "#8B0000",
                color: "#FFFFFF",
                fontSize: "14px",
                fontWeight: 700,
                cursor:
                  isCalculating || isCatalogLoading || !catalog
                    ? "wait"
                    : "pointer",
                fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
              }}
            >
              {isCalculating ? "Calcul en cours..." : "Calculer ma prime"}
            </button>
          </div>
        </div>


        {result && (
          <div
            aria-live="polite"
            style={{
              marginTop: "28px",
            }}
          >
            <div
              style={{
                padding: "20px 24px",
                borderRadius: "16px",
                background: result.eligible
                  ? "linear-gradient(135deg, #ECFDF5, #D1FAE5)"
                  : "linear-gradient(135deg, #FFF7ED, #FED7AA)",
                border: `1px solid ${
                  result.eligible
                    ? "#6EE7B7"
                    : "#FDBA74"
                }`,
                marginBottom: "20px",
                display: "flex",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <span style={{ fontSize: "28px" }}>
                {result.eligible ? "✅" : "⚠️"}
              </span>

              <div>
                <div
                  style={{
                    fontSize: "16px",
                    fontWeight: 800,
                    color: result.eligible
                      ? "#065F46"
                      : "#92400E",
                  }}
                >
                  {result.eligible
                    ? "Projet éligible au dispositif TPME"
                    : "Certaines conditions d'éligibilité ne sont pas remplies"}
                </div>

                <div
                  style={{
                    marginTop: "4px",
                    fontSize: "12px",
                    color: result.eligible
                      ? "#047857"
                      : "#9A3412",
                  }}
                >
                  Simulation indicative calculée à partir
                  des informations renseignées.
                </div>
              </div>
            </div>


            <div
              style={{
                display: "grid",
                gridTemplateColumns:
                  "repeat(auto-fill, minmax(190px, 1fr))",
                gap: "16px",
                marginBottom: "20px",
              }}
            >
              {[
                {
                  label: "Investissement total",
                  value: formatMad(
                    result.total_investment_mad
                  ),
                  color: "#0F172A",
                },
                {
                  label: "Investissement primable",
                  value: formatMad(
                    result.primable_investment_mad
                  ),
                  color: "#7C3AED",
                },
                {
                  label: "Ratio emplois",
                  value: formatRatio(
                    result.employment_ratio
                  ),
                  color: "#D97706",
                },
                {
                  label: "Taux total retenu",
                  value: `${result.total_rate_percent} %`,
                  color: "#1E3A8A",
                },
                {
                  label: "Prime totale estimée",
                  value: formatMad(
                    result.total_bonus_mad
                  ),
                  color: "#059669",
                },
              ].map((card) => (
                <div
                  key={card.label}
                  style={{
                    background: "#FFFFFF",
                    border: "1px solid #E2E8F0",
                    borderRadius: "14px",
                    padding: "20px",
                    boxShadow:
                      "0 2px 8px rgba(15,23,42,0.04)",
                  }}
                >
                  <div
                    style={{
                      fontSize: "11px",
                      color: "#64748B",
                      fontWeight: 700,
                      marginBottom: "8px",
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}
                  >
                    {card.label}
                  </div>

                  <div
                    style={{
                      fontSize: "19px",
                      fontWeight: 900,
                      color: card.color,
                    }}
                  >
                    {card.value}
                  </div>
                </div>
              ))}
            </div>


            {!result.eligible &&
              failedEligibility.length > 0 && (
                <div
                  style={{
                    background: "#FFFFFF",
                    border: "1px solid #FED7AA",
                    borderRadius: "16px",
                    overflow: "hidden",
                    marginBottom: "16px",
                  }}
                >
                  <div
                    style={{
                      padding: "16px 20px",
                      borderBottom:
                        "1px solid #FFF7ED",
                    }}
                  >
                    <h2
                      style={{
                        margin: 0,
                        fontSize: "15px",
                        fontWeight: 700,
                        color: "#9A3412",
                      }}
                    >
                      Conditions à vérifier
                    </h2>
                  </div>

                  {failedEligibility.map(
                    ([condition]) => (
                      <div
                        key={condition}
                        style={{
                          padding: "12px 20px",
                          borderBottom:
                            "1px solid #FFF7ED",
                          fontSize: "13px",
                          color: "#7C2D12",
                        }}
                      >
                        •{" "}
                        {eligibilityLabels[
                          condition
                        ] ?? condition}
                      </div>
                    )
                  )}
                </div>
              )}


            {result.details.length > 0 && (
              <div
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #E2E8F0",
                  borderRadius: "16px",
                  overflow: "hidden",
                  marginBottom: "16px",
                }}
              >
                <div
                  style={{
                    padding: "16px 20px",
                    borderBottom:
                      "1px solid #F1F5F9",
                  }}
                >
                  <h2
                    style={{
                      margin: 0,
                      fontSize: "15px",
                      fontWeight: 700,
                      color: "#0F172A",
                    }}
                  >
                    Détail des primes applicables
                  </h2>
                </div>

                {result.details.map(
                  (detail, index) => (
                    <div
                      key={detail.code}
                      style={{
                        display: "flex",
                        justifyContent:
                          "space-between",
                        alignItems: "center",
                        gap: "16px",
                        padding: "14px 20px",
                        borderBottom:
                          index <
                          result.details.length - 1
                            ? "1px solid #F8FAFC"
                            : "none",
                        background:
                          index % 2 === 0
                            ? "#FFFFFF"
                            : "#FAFBFC",
                      }}
                    >
                      <span
                        style={{
                          fontSize: "14px",
                          color: "#374151",
                        }}
                      >
                        {detail.label}
                      </span>

                      <span
                        style={{
                          fontSize: "15px",
                          fontWeight: 800,
                          color: "#1E3A8A",
                          background: "#EFF6FF",
                          padding: "4px 12px",
                          borderRadius: "9999px",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {detail.rate_percent} %
                      </span>
                    </div>
                  )
                )}
              </div>
            )}


            <div
              style={{
                background: "#FFFFFF",
                border: "1px solid #E2E8F0",
                borderRadius: "16px",
                overflow: "hidden",
                marginBottom: "16px",
              }}
            >
              <div
                style={{
                  padding: "16px 20px",
                  borderBottom:
                    "1px solid #F1F5F9",
                }}
              >
                <h2
                  style={{
                    margin: 0,
                    fontSize: "15px",
                    fontWeight: 700,
                    color: "#0F172A",
                  }}
                >
                  Calcul du montant primable
                </h2>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns:
                    "repeat(auto-fit, minmax(210px, 1fr))",
                  gap: "1px",
                  background: "#E2E8F0",
                }}
              >
                {[
                  {
                    label:
                      "Autres investissements retenus",
                    value:
                      result.primable_breakdown
                        .other_investment_mad,
                  },
                  {
                    label: "Études retenues",
                    value:
                      result.primable_breakdown
                        .eligible_studies_mad,
                  },
                  {
                    label: "Foncier retenu",
                    value:
                      result.primable_breakdown
                        .eligible_private_land_mad,
                  },
                  {
                    label: "Véhicules exclus",
                    value:
                      result.primable_breakdown
                        .excluded_vehicles_mad,
                  },
                  {
                    label:
                      "Dépenses liées exclues",
                    value:
                      result.primable_breakdown
                        .excluded_related_party_investment_mad,
                  },
                ].map((item) => (
                  <div
                    key={item.label}
                    style={{
                      background: "#FFFFFF",
                      padding: "16px 20px",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "11px",
                        color: "#64748B",
                        marginBottom: "5px",
                      }}
                    >
                      {item.label}
                    </div>

                    <div
                      style={{
                        fontSize: "14px",
                        fontWeight: 800,
                        color: "#0F172A",
                      }}
                    >
                      {formatMad(item.value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>


            {result.warnings.length > 0 && (
              <div
                style={{
                  background: "#FFFBEB",
                  border: "1px solid #FDE68A",
                  borderRadius: "14px",
                  padding: "16px 20px",
                }}
              >
                <h2
                  style={{
                    margin: "0 0 10px 0",
                    fontSize: "14px",
                    fontWeight: 700,
                    color: "#92400E",
                  }}
                >
                  Informations complémentaires
                </h2>

                {result.warnings.map(
                  (warning, index) => (
                    <div
                      key={`${warning}-${index}`}
                      style={{
                        fontSize: "12px",
                        color: "#92400E",
                        marginTop:
                          index === 0 ? 0 : "6px",
                      }}
                    >
                      • {warning}
                    </div>
                  )
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
