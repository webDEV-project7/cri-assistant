"use client";

import { useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";

import {
  auditInvestmentDossier,
  downloadInvestmentDossierReport,
  inspectInvestmentDocuments,
  type InvestmentDossierAuditResponse,
  type InvestmentDocumentInspectionResponse,
  type ProjectProfile,
  type RequirementAuditResult,
  type WorkType,
} from "@/lib/api";

const MAX_FILES = 10;
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024;

const ALLOWED_DOCUMENT_EXTENSIONS = [
  ".pdf",
  ".jpg",
  ".jpeg",
  ".png",
];

const ALLOWED_DOCUMENT_TYPES = new Set([
  "application/pdf",
  "image/jpeg",
  "image/jpg",
  "image/png",
]);

const initialProfile: ProjectProfile = {
  project_name: "",
  promoter_name: "",
  legal_form: "",
  sector: "",
  region: "Guelmim-Oued Noun",
  province: "Guelmim",
  commune: "Guelmim",
  investor_type: "societe_en_creation",
  land_status: "non_identifie",
  investment_amount_mad: 0,
  planned_jobs: 0,
  works: ["aucuns_travaux"],
  requests_incentives: false,
  requests_bank_financing: false,
  potential_environmental_impact: false,
  regulated_activity: false,
};

const workOptions: Array<{
  value: WorkType;
  label: string;
}> = [
  { value: "aucuns_travaux", label: "Sans travaux" },
  { value: "construction", label: "Construction" },
  { value: "extension", label: "Extension" },
  { value: "modification", label: "Modification ou réaménagement" },
  { value: "lotissement_morcellement", label: "Lotissement / morcellement" },
];

function formatFileSize(bytes: number): string {
  return (
    new Intl.NumberFormat("fr-FR", {
      maximumFractionDigits: 1,
    }).format(bytes / (1024 * 1024)) + " Mo"
  );
}

function levelLabel(
  level: RequirementAuditResult["requirement"]["level"],
): string {
  const labels = {
    obligatoire: "Obligatoire",
    conditionnelle: "Conditionnelle",
    recommandee: "Recommandée",
  };
  return labels[level];
}

type ManualClassifications = Record<string, string[]>;

function hasManualClassification(
  manualClassifications: ManualClassifications,
  filename: string,
): boolean {
  return Object.prototype.hasOwnProperty.call(
    manualClassifications,
    filename,
  );
}

function applyManualClassifications(
  response: InvestmentDossierAuditResponse,
  manualClassifications: ManualClassifications,
): InvestmentDossierAuditResponse {
  const requirementsByCode = new Map(
    response.audit.results.map((item) => [
      item.requirement.code,
      item.requirement,
    ]),
  );

  const documents = response.documents.map((document) => {
    if (!hasManualClassification(manualClassifications, document.filename)) {
      return document;
    }

    const selectedCodes = manualClassifications[document.filename].filter((code) =>
      requirementsByCode.has(code),
    );
    const selectedLabels = selectedCodes.map(
      (code) => requirementsByCode.get(code)?.label ?? code,
    );

    if (selectedCodes.length === 0) {
      return {
        ...document,
        classification: {
          ...document.classification,
          status: "non_classe" as const,
          requirement_code: null,
          confidence: 1,
          explanation: "Aucun type confirmé manuellement.",
        },
      };
    }

    return {
      ...document,
      classification: {
        ...document.classification,
        status: "classe" as const,
        requirement_code: selectedCodes[0],
        confidence: 1,
        explanation:
          selectedCodes.length === 1
            ? `Type confirmé manuellement : ${selectedLabels[0]}.`
            : `Types confirmés manuellement : ${selectedLabels.join(", ")}.`,
      },
    };
  });

  const filenamesByCode = new Map<string, string[]>();
  const unclassifiedDocuments: string[] = [];
  const unknownRequirementCodes = new Set<string>();

  for (const document of documents) {
    const isManual = hasManualClassification(
      manualClassifications,
      document.filename,
    );
    const requirementCodes = isManual
      ? manualClassifications[document.filename]
      : document.classification.status === "classe" &&
          document.classification.requirement_code
        ? [document.classification.requirement_code]
        : [];

    if (requirementCodes.length === 0) {
      unclassifiedDocuments.push(document.filename);
      continue;
    }

    for (const requirementCode of requirementCodes) {
      if (!requirementsByCode.has(requirementCode)) {
        unknownRequirementCodes.add(requirementCode);
        continue;
      }

      const submittedFiles = filenamesByCode.get(requirementCode) ?? [];
      if (!submittedFiles.includes(document.filename)) {
        submittedFiles.push(document.filename);
      }
      filenamesByCode.set(requirementCode, submittedFiles);
    }
  }

  const auditResults = response.audit.results.map((item) => {
    const submittedFiles = filenamesByCode.get(item.requirement.code) ?? [];
    return {
      ...item,
      status:
        submittedFiles.length > 0
          ? ("presente_non_verifiee" as const)
          : item.requirement.level === "recommandee"
            ? ("recommandee_absente" as const)
            : ("manquante" as const),
      submitted_files: submittedFiles,
    };
  });

  const scoredResults = auditResults.filter(
    (item) => item.requirement.level !== "recommandee",
  );
  const presentScoredCount = scoredResults.filter(
    (item) => item.status === "presente_non_verifiee",
  ).length;

  const completenessPercentage =
    scoredResults.length > 0
      ? (presentScoredCount / scoredResults.length) * 100
      : 100;

  const missingRequiredCount = auditResults.filter(
    (item) =>
      item.requirement.level === "obligatoire" && item.status === "manquante",
  ).length;

  return {
    ...response,
    documents,
    audit: {
      ...response.audit,
      summary: {
        ...response.audit.summary,
        completeness_percentage: completenessPercentage,
        present_requirement_count: presentScoredCount,
        missing_required_count: missingRequiredCount,
        unclassified_document_count: unclassifiedDocuments.length,
      },
      results: auditResults,
    },
  };
}

function RequirementList({
  title,
  items,
  tone,
}: {
  title: string;
  items: RequirementAuditResult[];
  tone: "success" | "danger" | "warning";
}) {
  if (items.length === 0) return null;

  const badgeBg =
    tone === "success"
      ? "#DCFCE7"
      : tone === "danger"
        ? "#FEE2E2"
        : "#FEF3C7";
  const badgeColor =
    tone === "success"
      ? "#166534"
      : tone === "danger"
        ? "#991B1B"
        : "#92400E";
  const borderColor =
    tone === "success"
      ? "#86EFAC"
      : tone === "danger"
        ? "#FCA5A5"
        : "#FDE68A";

  return (
    <div
      style={{
        background: "#FFFFFF",
        borderRadius: "16px",
        border: `1.5px solid ${borderColor}`,
        padding: "20px 24px",
        marginBottom: "16px",
        boxShadow: "0 2px 10px rgba(0,0,0,0.03)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          marginBottom: "14px",
        }}
      >
        <span
          style={{
            background: badgeBg,
            color: badgeColor,
            fontWeight: 800,
            fontSize: "12px",
            padding: "4px 10px",
            borderRadius: "9999px",
            fontFamily: "var(--font-montserrat), sans-serif",
          }}
        >
          {items.length}
        </span>
        <h3
          style={{
            fontFamily: "var(--font-montserrat), sans-serif",
            fontSize: "16px",
            fontWeight: 800,
            color: "#1A1A1A",
            margin: 0,
          }}
        >
          {title}
        </h3>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {items.map((item) => (
          <div
            key={item.requirement.code}
            style={{
              background: "#FAF6F0",
              borderRadius: "12px",
              padding: "14px 16px",
              border: "1px solid #EADECF",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: "4px",
              }}
            >
              <strong style={{ fontSize: "14px", color: "#1A1A1A" }}>
                {item.requirement.label}
              </strong>
              <span
                style={{
                  fontSize: "11px",
                  color: "#666",
                  background: "#FFFFFF",
                  padding: "2px 8px",
                  borderRadius: "6px",
                  border: "1px solid #EADECF",
                }}
              >
                {levelLabel(item.requirement.level)}
              </span>
            </div>
            <p style={{ fontSize: "13px", color: "#555", margin: "4px 0 0 0", lineHeight: 1.5 }}>
              {item.requirement.reason}
            </p>
            {item.submitted_files.length > 0 && (
              <div
                style={{
                  fontSize: "12px",
                  color: "#008751",
                  marginTop: "6px",
                  fontWeight: 600,
                }}
              >
                📁 Fichier(s) associé(s) : {item.submitted_files.join(", ")}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

type DocumentAuditProps = {
  onDiscussAnalysis?: (
    analysisContext: string,
    introduction: string,
    suggestedQuestions: string[],
  ) => void;
};

function buildDocumentAnalysisContext(
  result: InvestmentDossierAuditResponse,
): string {
  const profile = result.audit.project_profile;
  const summary = result.audit.summary;

  const presentRequirements = result.audit.results.filter(
    (item) => item.status === "presente_non_verifiee",
  );

  const missingRequirements = result.audit.results.filter(
    (item) => item.status === "manquante",
  );

  const recommendedAbsent = result.audit.results.filter(
    (item) => item.status === "recommandee_absente",
  );

  const lines: string[] = [
    "RÉSUMÉ STRUCTURÉ DE L'ANALYSE DOCUMENTAIRE",
    "",
    "PROFIL DU PROJET",
    `Projet : ${profile.project_name || "non précisé"}`,
    `Porteur : ${profile.promoter_name || "non précisé"}`,
    `CIN / Passeport : ${profile.identity_document_number || "non précisé"}`,
    `Forme juridique : ${profile.legal_form || "non précisée"}`,
    `Secteur : ${profile.sector || "non précisé"}`,
    `Région : ${profile.region || "non précisée"}`,
    `Province : ${profile.province || "non précisée"}`,
    `Commune : ${profile.commune || "non précisée"}`,
    `Montant d'investissement : ${profile.investment_amount_mad} MAD`,
    `Emplois prévus : ${profile.planned_jobs}`,
    `Travaux : ${profile.works.join(", ") || "non précisés"}`,
    "",
    "SYNTHÈSE",
    `Score de complétude : ${Math.round(
      summary.completeness_percentage,
    )}%`,
    `Documents transmis : ${summary.submitted_document_count}`,
    `Pièces détectées : ${summary.present_requirement_count}`,
    `Pièces obligatoires manquantes : ${summary.missing_required_count}`,
    `Pièces conditionnelles manquantes : ${summary.missing_conditional_count}`,
    `Documents non classés : ${summary.unclassified_document_count}`,
    `Doublons détectés : ${summary.duplicate_requirement_count}`,
    "",
    "DOCUMENTS ANALYSÉS",
  ];

  for (const document of result.documents) {
    const classification = document.classification;

    lines.push(
      [
        `- Fichier : ${document.filename}`,
        `pages=${document.page_count}`,
        `statut=${classification.status}`,
        `code=${classification.requirement_code ?? "aucun"}`,
        `confiance=${classification.confidence}`,
        `explication=${classification.explanation}`,
      ].join(" ; "),
    );
  }

  lines.push("", "PIÈCES PRÉSENTES MAIS NON VALIDÉES");

  if (presentRequirements.length === 0) {
    lines.push("- Aucune pièce détectée.");
  } else {
    for (const item of presentRequirements) {
      lines.push(
        `- ${item.requirement.label} : ${
          item.submitted_files.join(", ") || "fichier non précisé"
        }`,
      );
    }
  }

  lines.push("", "PIÈCES MANQUANTES");

  if (missingRequirements.length === 0) {
    lines.push("- Aucune pièce obligatoire ou conditionnelle manquante.");
  } else {
    for (const item of missingRequirements) {
      lines.push(
        `- ${item.requirement.label} `
        + `(${item.requirement.level}) : `
        + `${item.requirement.reason}`,
      );
    }
  }

  lines.push("", "PIÈCES RECOMMANDÉES ABSENTES");

  if (recommendedAbsent.length === 0) {
    lines.push("- Aucune.");
  } else {
    for (const item of recommendedAbsent) {
      lines.push(
        `- ${item.requirement.label} : ${item.requirement.reason}`,
      );
    }
  }

  lines.push("", "DOCUMENTS NON CLASSÉS");

  if (result.audit.unclassified_documents.length === 0) {
    lines.push("- Aucun.");
  } else {
    for (
      const filename
      of result.audit.unclassified_documents
    ) {
      lines.push(`- ${filename}`);
    }
  }

  lines.push(
    "",
    "AVERTISSEMENT",
    result.audit.warning,
  );

  return lines.join("\n").slice(0, 11000);
}



function buildDocumentAnalysisIntroduction(
  result: InvestmentDossierAuditResponse,
): string {
  const summary = result.audit.summary;

  const unclassifiedCount =
    result.audit.unclassified_documents.length;

  const missingCount =
    summary.missing_required_count
    + summary.missing_conditional_count;

  const projectName =
    result.audit.project_profile.project_name
    || "Projet sans nom précisé";

  const lines = [
    "J’ai reçu l’analyse de votre dossier.",
    "",
    `Projet : ${projectName}`,
    `Score de complétude : ${Math.round(
      summary.completeness_percentage,
    )} %`,
    `Documents transmis : ${
      summary.submitted_document_count
    }`,
    `Pièces détectées : ${
      summary.present_requirement_count
    }`,
    `Pièces manquantes : ${missingCount}`,
    `Documents non classés : ${unclassifiedCount}`,
    "",
    (
      "Sélectionnez une question ci-dessous "
      + "ou écrivez votre propre demande."
    ),
  ];

  return lines.join("\n");
}


function buildDocumentAnalysisQuestions(
  result: InvestmentDossierAuditResponse,
): string[] {
  const questions: string[] = [];

  const missingRequirements =
    result.audit.results.filter(
      (item) => item.status === "manquante",
    );

  const recommendedRequirements =
    result.audit.results.filter(
      (item) =>
        item.status === "recommandee_absente",
    );

  const unclassifiedDocuments =
    result.audit.unclassified_documents;

  function addQuestion(
    question: string,
  ): void {
    const normalizedQuestion =
      question.trim();

    if (!normalizedQuestion) {
      return;
    }

    if (questions.includes(normalizedQuestion)) {
      return;
    }

    questions.push(normalizedQuestion);
  }

  if (unclassifiedDocuments.length > 0) {
    const firstFilename =
      unclassifiedDocuments[0];

    addQuestion(
      `Pourquoi le document « ${firstFilename} » `
      + "n’a-t-il pas été reconnu ?",
    );
  }

  if (missingRequirements.length > 0) {
    addQuestion(
      "Quelles pièces dois-je ajouter en priorité ?",
    );

    for (
      const item
      of missingRequirements.slice(0, 2)
    ) {
      addQuestion(
        `Comment préparer « ${
          item.requirement.label
        } » ?`,
      );
    }
  }

  if (recommendedRequirements.length > 0) {
    addQuestion(
      "Quelles pièces recommandées peuvent "
      + "renforcer mon dossier ?",
    );
  }

  if (
    result.audit.project_profile
      .requests_incentives
  ) {
    addQuestion(
      "Quelles pièces sont nécessaires "
      + "pour ma demande de prime ?",
    );
  }

  if (
    result.audit.project_profile
      .requests_bank_financing
  ) {
    addQuestion(
      "Quels documents dois-je préparer "
      + "pour le financement bancaire ?",
    );
  }

  if (
    result.audit.summary
      .completeness_percentage < 100
  ) {
    addQuestion(
      "Comment améliorer le score "
      + "de complétude de mon dossier ?",
    );
  }

  if (
    result.audit.project_profile
      .investor_type
    === "societe_en_creation"
  ) {
    addQuestion(
      "Quelles pièces faut-il pour "
      + "une société en création ?",
    );
  }

  if (questions.length === 0) {
    addQuestion(
      "Pouvez-vous m’expliquer le résultat "
      + "de cette analyse ?",
    );

    addQuestion(
      "Quelles sont les prochaines étapes "
      + "pour mon dossier ?",
    );
  }

  return questions.slice(0, 5);
}


export default function DocumentAudit({
  onDiscussAnalysis,
}: DocumentAuditProps) {
  type AuditStage =
    | "documents"
    | "profile"
    | "results";

  const [stage, setStage] =
    useState<AuditStage>("documents");

  const [profile, setProfile] =
    useState<ProjectProfile>(initialProfile);

  const [files, setFiles] =
    useState<File[]>([]);

  const [inspection, setInspection] =
    useState<InvestmentDocumentInspectionResponse | null>(
      null,
    );

  const [sourceResult, setSourceResult] =
    useState<InvestmentDossierAuditResponse | null>(
      null,
    );

  const [
    manualClassifications,
    setManualClassifications,
  ] = useState<ManualClassifications>({});

  const [showProfileForm, setShowProfileForm] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [isInspecting, setIsInspecting] =
    useState(false);

  const [isAuditing, setIsAuditing] =
    useState(false);

  const [
    isDownloadingReport,
    setIsDownloadingReport,
  ] = useState(false);

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  const cameraInputRef =
    useRef<HTMLInputElement>(null);

  const result = useMemo(
    () =>
      sourceResult
        ? applyManualClassifications(
            sourceResult,
            manualClassifications,
          )
        : null,
    [
      sourceResult,
      manualClassifications,
    ],
  );

  const presentResults =
    result?.audit.results.filter(
      (item) =>
        item.status ===
        "presente_non_verifiee",
    ) ?? [];

  const missingResults =
    result?.audit.results.filter(
      (item) =>
        item.status === "manquante",
    ) ?? [];

  const recommendedResults =
    result?.audit.results.filter(
      (item) =>
        item.status ===
        "recommandee_absente",
    ) ?? [];

  const availableRequirements =
    result?.audit.results
      .map((item) => item.requirement)
      .sort((first, second) =>
        first.label.localeCompare(
          second.label,
          "fr",
        ),
      ) ?? [];

  const cardStyle = {
    background: "#FFFFFF",
    borderRadius: "20px",
    padding: "28px",
    border: "1px solid #EADECF",
    boxShadow:
      "0 5px 22px rgba(0,0,0,0.05)",
  } as const;

  const labelStyle = {
    display: "block",
    fontSize: "13px",
    fontWeight: 700,
    color: "#333333",
    marginBottom: "6px",
  } as const;

  const inputStyle = {
    width: "100%",
    padding: "11px 13px",
    borderRadius: "10px",
    border: "1.5px solid #CBD5E1",
    background: "#FFFFFF",
    fontSize: "14px",
    boxSizing: "border-box",
    outline: "none",
  } as const;

  const missingFieldLabels: Record<
    string,
    string
  > = {
    project_name: "Nom du projet",
    promoter_name:
      "Porteur du projet ou société",
    sector: "Secteur d’activité",
    investment_amount_mad:
      "Montant de l’investissement",
    planned_jobs: "Emplois prévus",
    investor_type: "Type d’investisseur",
    land_status: "Situation foncière",
    works: "Nature des travaux",
    province: "Province",
    commune: "Commune",
  };

  function resetResults(): void {
    setInspection(null);
    setSourceResult(null);
    setManualClassifications({});
  }

  function validateSelectedFiles(
    selectedFiles: File[],
  ): string | null {
    if (selectedFiles.length > MAX_FILES) {
      return (
        `Vous pouvez sélectionner au maximum `
        + `${MAX_FILES} documents.`
      );
    }

    const invalidType = selectedFiles.find(
      (file) => {
        const lowerName =
          file.name.toLowerCase();

        const hasAllowedExtension =
          ALLOWED_DOCUMENT_EXTENSIONS.some(
            (extension) =>
              lowerName.endsWith(extension),
          );

        const hasAllowedType =
          !file.type
          || ALLOWED_DOCUMENT_TYPES.has(
            file.type,
          );

        return (
          !hasAllowedExtension
          || !hasAllowedType
        );
      },
    );

    if (invalidType) {
      return (
        `Le format du fichier « `
        + `${invalidType.name} » `
        + "n’est pas accepté. "
        + "Formats autorisés : "
        + "PDF, JPG, JPEG et PNG."
      );
    }

    const emptyFile = selectedFiles.find(
      (file) => file.size === 0,
    );

    if (emptyFile) {
      return (
        `Le fichier « ${emptyFile.name} » `
        + "est vide."
      );
    }

    const oversizedFile =
      selectedFiles.find(
        (file) =>
          file.size
          > MAX_FILE_SIZE_BYTES,
      );

    if (oversizedFile) {
      return (
        `Le fichier « `
        + `${oversizedFile.name} » `
        + "dépasse la limite de 10 Mo."
      );
    }

    return null;
  }

  function addFiles(
    selectedFiles: File[],
  ): void {
    setError(null);

    const mergedFiles = [
      ...files,
      ...selectedFiles,
    ];

    const uniqueFiles =
      mergedFiles.filter(
        (file, index, allFiles) =>
          allFiles.findIndex(
            (candidate) =>
              candidate.name === file.name
              && candidate.size === file.size
              && candidate.lastModified
                === file.lastModified,
          ) === index,
      );

    const validationError =
      validateSelectedFiles(uniqueFiles);

    if (validationError) {
      setError(validationError);
      return;
    }

    setFiles(uniqueFiles);
    resetResults();
    setStage("documents");
  }

  function removeFile(
    index: number,
  ): void {
    setFiles((current) =>
      current.filter(
        (_, fileIndex) =>
          fileIndex !== index,
      ),
    );

    resetResults();
    setStage("documents");
    setError(null);
  }

  function resetAudit(): void {
    setStage("documents");
    setProfile(initialProfile);
    setFiles([]);
    resetResults();
    setError(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    if (cameraInputRef.current) {
      cameraInputRef.current.value = "";
    }
  }

  function selectWork(
    work: WorkType,
  ): void {
    setProfile((current) => ({
      ...current,
      works: [work],
    }));
  }

  function applyDetectedProfile(
    response:
      InvestmentDocumentInspectionResponse,
  ): void {
    const detected =
      response.detected_profile;

    setProfile((current) => ({
      ...current,
      project_name:
        detected.project_name
        ?? current.project_name,
      promoter_name:
        detected.promoter_name
        ?? current.promoter_name,
      legal_form:
        detected.legal_form
        ?? current.legal_form,
      sector:
        detected.sector
        ?? current.sector,
      region:
        detected.region
        ?? current.region,
      province:
        detected.province
        ?? current.province,
      commune:
        detected.commune
        ?? current.commune,
      investor_type:
        detected.investor_type
        ?? current.investor_type,
      land_status:
        detected.land_status
        ?? current.land_status,
      investment_amount_mad:
        detected.investment_amount_mad
        ?? current.investment_amount_mad,
      planned_jobs:
        detected.planned_jobs
        ?? current.planned_jobs,
      works:
        detected.works.length > 0
          ? detected.works
          : current.works,
    }));
  }

  async function handleInspectDocuments():
    Promise<void> {
    setError(null);

    if (files.length === 0) {
      setError(
        "Ajoutez au moins un PDF ou une image.",
      );
      return;
    }

    setIsInspecting(true);
    setSourceResult(null);
    setManualClassifications({});

    try {
      const response =
        await inspectInvestmentDocuments(
          files,
        );

      setInspection(response);
      applyDetectedProfile(response);
      setStage("profile");

    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : (
              "Une erreur est survenue "
              + "pendant la pré-analyse OCR."
            ),
      );

    } finally {
      setIsInspecting(false);
    }
  }

  function profileIsReady(): boolean {
    return (
      profile.sector.trim().length >= 2
      && profile.region.trim().length >= 2
      && profile.province.trim().length >= 2
      && profile.commune.trim().length >= 2
      && profile.investment_amount_mad > 0
      && profile.planned_jobs >= 0
    );
  }

  async function handleFinalAudit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    setError(null);

    if (!profileIsReady()) {
      setError(
        "Complétez au minimum le secteur, "
        + "la localisation et le montant "
        + "de l’investissement avant "
        + "l’audit complet.",
      );
      return;
    }

    setIsAuditing(true);
    setSourceResult(null);
    setManualClassifications({});

    try {
      const response =
        await auditInvestmentDossier(
          profile,
          files,
        );

      setSourceResult(response);

      window.setTimeout(() => {
        document
          .getElementById(
            "audit-complete-actions",
          )
          ?.scrollIntoView({
            behavior: "smooth",
            block: "center",
          });
      }, 100);

    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : (
              "Une erreur est survenue "
              + "pendant l’audit complet."
            ),
      );

    } finally {
      setIsAuditing(false);
    }
  }

  async function handleDownloadReport():
    Promise<void> {
    setError(null);

    if (!result) {
      setError(
        "Aucun résultat d’audit n’est disponible.",
      );
      return;
    }

    setIsDownloadingReport(true);

    try {
      await downloadInvestmentDossierReport(
        result,
      );

    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : (
              "La génération du rapport PDF "
              + "a échoué."
            ),
      );

    } finally {
      setIsDownloadingReport(false);
    }
  }


  function fieldWasDetected(
    fieldName: string,
  ): boolean {
    return Boolean(
      inspection?.field_sources[
        fieldName
      ]?.length,
    );
  }

  function renderDetectionBadge(fieldName: string) {
    const detected =
      fieldWasDetected(fieldName);

    if (detected) {
      return null;
    }

    return (
      <span
        style={{
          marginLeft: "8px",
          padding: "2px 7px",
          borderRadius: "9999px",
          fontSize: "10px",
          fontWeight: 800,
          color: detected
            ? "#047857"
            : "#92400E",
          background: detected
            ? "#D1FAE5"
            : "#FEF3C7",
        }}
      >
        {detected
          ? "Détecté par OCR"
          : "À compléter"}
      </span>
    );
  }

  function selectedDocumentCodes(
    document:
      InvestmentDossierAuditResponse[
        "documents"
      ][number],
  ): string[] {
    if (
      hasManualClassification(
        manualClassifications,
        document.filename,
      )
    ) {
      return manualClassifications[
        document.filename
      ];
    }

    return (
      document.classification.status
        === "classe"
      && document.classification
        .requirement_code
    )
      ? [
          document.classification
            .requirement_code,
        ]
      : [];
  }

  function toggleDocumentType(
    document:
      InvestmentDossierAuditResponse[
        "documents"
      ][number],
    requirementCode: string,
    checked: boolean,
  ): void {
    setManualClassifications(
      (current) => {
        const existingCodes =
          hasManualClassification(
            current,
            document.filename,
          )
            ? current[document.filename]
            : (
                document.classification
                  .status === "classe"
                && document.classification
                  .requirement_code
              )
              ? [
                  document.classification
                    .requirement_code,
                ]
              : [];

        const updatedCodes =
          checked
            ? Array.from(
                new Set([
                  ...existingCodes,
                  requirementCode,
                ]),
              )
            : existingCodes.filter(
                (code) =>
                  code !== requirementCode,
              );

        return {
          ...current,
          [document.filename]:
            updatedCodes,
        };
      },
    );
  }

  function restoreAutomaticClassification(
    filename: string,
  ): void {
    setManualClassifications(
      (current) => {
        const updated = {
          ...current,
        };

        delete updated[filename];

        return updated;
      },
    );
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#FAF6F0",
        fontFamily:
          "var(--font-inter), sans-serif",
      }}
    >
      <div
        style={{
          background:
            "linear-gradient(135deg, "
            + "#4A0404 0%, "
            + "#8B0000 60%, "
            + "#B91C1C 100%)",
          padding: "26px 32px 30px",
          color: "#FFFFFF",
        }}
      >
        <div
          style={{
            maxWidth: "1500px",
            margin: "0 auto",
          }}
        >
          <nav
            style={{
              marginBottom: "14px",
              fontSize: "13px",
              color:
                "rgba(255,255,255,0.75)",
            }}
          >
            Services numériques
            <span
              style={{
                margin: "0 6px",
              }}
            >
              /
            </span>
            <span
              style={{
                color: "#FCD34D",
                fontWeight: 700,
              }}
            >
              Pré-analyse documentaire
            </span>
          </nav>

          <h1
            style={{
              margin: "0 0 10px 0",
              fontSize:
                "clamp(27px,4vw,40px)",
              fontWeight: 900,
              fontFamily:
                "var(--font-montserrat), "
                + "sans-serif",
            }}
          >
            Analyse documentaire
          </h1>

          <p
            style={{
              maxWidth: "760px",
              margin: 0,
              fontSize: "15px",
              lineHeight: 1.7,
              color:
                "rgba(255,255,255,0.9)",
            }}
          >
            Ajoutez d’abord vos documents.
            L’OCR détectera les informations
            disponibles, puis vous pourrez
            vérifier et compléter uniquement
            les éléments manquants.
          </p>
        </div>
      </div>

      <main
        style={{
          maxWidth: "1500px",
          margin: "28px auto 60px",
          padding: "0 18px",
        }}
      >
        <div
          style={{
            ...cardStyle,
            padding: "18px 24px",
            marginBottom: "22px",
            display: "grid",
            gridTemplateColumns:
              "repeat(2, 1fr)",
            gap: "10px",
          }}
        >
          {[
            {
              key: "documents",
              number: "1",
              label:
                "Ajouter les documents",
            },
            {
              key: "profile",
              number: "2",
              label:
                "Vérifier les informations",
            },
                      ].map((step) => {
            const stageOrder = {
              documents: 0,
              profile: 1,
              results: 2,
            };

            const isActive =
              stage === step.key;

            const isCompleted =
              stageOrder[stage]
              > stageOrder[
                step.key as AuditStage
              ];

            return (
              <div
                key={step.key}
                style={{
                  padding: "10px 12px",
                  borderRadius: "12px",
                  textAlign: "center",
                  background:
                    isActive
                      ? "#FEF2F2"
                      : isCompleted
                        ? "#ECFDF5"
                        : "#F8FAFC",
                  border:
                    isActive
                      ? "1px solid #FCA5A5"
                      : isCompleted
                        ? "1px solid #A7F3D0"
                        : "1px solid #E2E8F0",
                  color:
                    isActive
                      ? "#8B0000"
                      : isCompleted
                        ? "#047857"
                        : "#64748B",
                  fontSize: "12px",
                  fontWeight: 800,
                }}
              >
                {step.number}. {step.label}
              </div>
            );
          })}
        </div>

        {error && (
          <div
            role="alert"
            style={{
              marginBottom: "20px",
              padding: "14px 18px",
              borderRadius: "12px",
              color: "#991B1B",
              background: "#FEE2E2",
              border: "1px solid #FCA5A5",
              fontSize: "13px",
              fontWeight: 700,
            }}
          >
            {error}
          </div>
        )}

        {stage === "documents" && (
          <section
            style={{
              display: "grid",
              gap: "22px",
            }}
          >
            <div
              style={{
                maxWidth: "1180px",
              }}
            >
              <div
                style={{
                  color: "#C77700",
                  fontSize: "11px",
                  fontWeight: 900,
                  letterSpacing: "0.14em",
                  textTransform: "uppercase",
                  marginBottom: "8px",
                }}
              >
                Pré-analyse documentaire
              </div>

              <h1
                style={{
                  margin: 0,
                  color: "#1C1917",
                  fontFamily:
                    "var(--font-fraunces), Georgia, serif",
                  fontSize:
                    "clamp(30px, 3.4vw, 44px)",
                  lineHeight: 1.08,
                  fontWeight: 700,
                  letterSpacing: "-0.03em",
                }}
              >
                Préparez un dossier plus complet,
                dès la première étape.
              </h1>

              <p
                style={{
                  margin: "10px 0 0 0",
                  maxWidth: "730px",
                  color: "#64748B",
                  fontSize: "14px",
                  lineHeight: 1.65,
                }}
              >
                Déposez vos documents pour obtenir une
                première vérification de leur complétude
                et de leur cohérence avant vos démarches
                auprès du CRI.
              </p>
            </div>


            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                gap: "20px",
                flexWrap: "wrap",
              }}
            >
              <div
                style={{
                  flex: "1 1 880px",
                  minWidth: 0,
                  background: "#FFFFFF",
                  border: "1px solid #E7E5E4",
                  borderRadius: "14px",
                  padding: "18px",
                  boxShadow:
                    "0 8px 28px rgba(28,25,23,0.06)",
                }}
              >
                <div
                  onDragOver={(event) => {
                    event.preventDefault();
                  }}
                  onDrop={(event) => {
                    event.preventDefault();

                    if (isInspecting) {
                      return;
                    }

                    addFiles(
                      Array.from(
                        event.dataTransfer.files ?? [],
                      ),
                    );
                  }}
                  style={{
                    minHeight: "310px",
                    border: "1.5px dashed #15805B",
                    borderRadius: "11px",
                    background:
                      "linear-gradient(180deg, #FFFFFF, #FFFEFA)",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    justifyContent: "center",
                    textAlign: "center",
                    padding: "34px 24px",
                  }}
                >
                  <div
                    style={{
                      width: "58px",
                      height: "68px",
                      position: "relative",
                      marginBottom: "17px",
                    }}
                  >
                    <svg
                      width="58"
                      height="68"
                      viewBox="0 0 58 68"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path
                        d="M10 2H37L56 21V64C56 65.1 55.1 66 54 66H10C8.9 66 8 65.1 8 64V4C8 2.9 8.9 2 10 2Z"
                        stroke="#08794F"
                        strokeWidth="2.4"
                      />
                      <path
                        d="M37 2V21H56"
                        stroke="#08794F"
                        strokeWidth="2.4"
                      />
                      <path
                        d="M19 35H45"
                        stroke="#08794F"
                        strokeWidth="2.4"
                        strokeLinecap="round"
                      />
                      <path
                        d="M19 45H45"
                        stroke="#08794F"
                        strokeWidth="2.4"
                        strokeLinecap="round"
                      />
                      <path
                        d="M19 55H39"
                        stroke="#08794F"
                        strokeWidth="2.4"
                        strokeLinecap="round"
                      />
                    </svg>
                  </div>

                  <h2
                    style={{
                      margin: 0,
                      color: "#14613F",
                      fontFamily:
                        "var(--font-fraunces), Georgia, serif",
                      fontSize: "24px",
                      lineHeight: 1.2,
                      fontWeight: 700,
                    }}
                  >
                    Ajoutez vos documents
                  </h2>

                  <p
                    style={{
                      margin: "8px 0 20px 0",
                      color: "#78716C",
                      fontSize: "12px",
                      lineHeight: 1.55,
                    }}
                  >
                    Sélectionnez ou déposez vos fichiers
                    pour une première vérification.
                  </p>

                  <button
                    type="button"
                    onClick={() =>
                      fileInputRef.current?.click()
                    }
                    disabled={isInspecting}
                    style={{
                      width: "100%",
                      maxWidth: "390px",
                      border: "1.5px solid #08794F",
                      borderRadius: "7px",
                      padding: "12px 18px",
                      background: "#FFFFFF",
                      color: "#08794F",
                      fontSize: "13px",
                      fontWeight: 850,
                      cursor: isInspecting
                        ? "not-allowed"
                        : "pointer",
                    }}
                  >
                    ↑&nbsp;&nbsp; Sélectionner des fichiers
                  </button>

                  <button
                    type="button"
                    onClick={() =>
                      cameraInputRef.current?.click()
                    }
                    disabled={isInspecting}
                    style={{
                      marginTop: "10px",
                      border: "none",
                      background: "transparent",
                      color: "#64748B",
                      fontSize: "11px",
                      fontWeight: 750,
                      cursor: isInspecting
                        ? "not-allowed"
                        : "pointer",
                      textDecoration: "underline",
                      textUnderlineOffset: "3px",
                    }}
                  >
                    Prendre une photo
                  </button>

                  <input
                    ref={cameraInputRef}
                    type="file"
                    accept={
                      ".jpg,.jpeg,.png,"
                      + "image/jpeg,image/png"
                    }
                    capture="environment"
                    style={{ display: "none" }}
                    onChange={(event) => {
                      addFiles(
                        Array.from(
                          event.target.files ?? [],
                        ),
                      );

                      event.currentTarget.value = "";
                    }}
                  />

                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept={
                      ".pdf,.jpg,.jpeg,.png,"
                      + "application/pdf,"
                      + "image/jpeg,image/png"
                    }
                    style={{ display: "none" }}
                    onChange={(event) => {
                      addFiles(
                        Array.from(
                          event.target.files ?? [],
                        ),
                      );

                      event.currentTarget.value = "";
                    }}
                  />

                  <p
                    style={{
                      margin: "18px 0 0 0",
                      color: "#78716C",
                      fontSize: "11px",
                    }}
                  >
                    PDF, JPG, JPEG, PNG
                    {" • "}
                    10 documents maximum
                    {" • "}
                    10 Mo maximum par fichier
                  </p>
                </div>


                {files.length > 0 && (
                  <div
                    style={{
                      marginTop: "17px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent:
                          "space-between",
                        gap: "12px",
                        marginBottom: "10px",
                      }}
                    >
                      <h3
                        style={{
                          margin: 0,
                          color: "#292524",
                          fontFamily:
                            "var(--font-fraunces), Georgia, serif",
                          fontSize: "17px",
                          fontWeight: 700,
                        }}
                      >
                        Documents sélectionnés
                      </h3>

                      <span
                        style={{
                          borderRadius: "9999px",
                          background: "#ECFDF5",
                          color: "#047857",
                          padding: "4px 9px",
                          fontSize: "10px",
                          fontWeight: 850,
                        }}
                      >
                        {files.length}
                        {" / "}
                        {MAX_FILES}
                      </span>
                    </div>

                    <div
                      style={{
                        display: "grid",
                        gap: "7px",
                      }}
                    >
                      {files.map((file, index) => (
                        <div
                          key={
                            `${file.name}-`
                            + `${file.size}-`
                            + `${index}`
                          }
                          style={{
                            display: "flex",
                            justifyContent:
                              "space-between",
                            alignItems: "center",
                            gap: "12px",
                            padding: "10px 12px",
                            borderRadius: "8px",
                            background: "#FAFAF9",
                            border:
                              "1px solid #E7E5E4",
                          }}
                        >
                          <div
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "10px",
                              minWidth: 0,
                            }}
                          >
                            <span
                              style={{
                                width: "31px",
                                height: "36px",
                                borderRadius: "5px",
                                background: "#F0FDF4",
                                border:
                                  "1px solid #BBF7D0",
                                color: "#047857",
                                display: "inline-flex",
                                alignItems: "center",
                                justifyContent: "center",
                                flexShrink: 0,
                                fontSize: "14px",
                              }}
                            >
                              ▤
                            </span>

                            <div
                              style={{
                                minWidth: 0,
                              }}
                            >
                              <div
                                style={{
                                  color: "#292524",
                                  fontSize: "11px",
                                  fontWeight: 800,
                                  overflow: "hidden",
                                  textOverflow:
                                    "ellipsis",
                                  whiteSpace: "nowrap",
                                }}
                              >
                                {file.name}
                              </div>

                              <div
                                style={{
                                  marginTop: "2px",
                                  color: "#94A3B8",
                                  fontSize: "9px",
                                }}
                              >
                                {formatFileSize(
                                  file.size,
                                )}
                              </div>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() =>
                              removeFile(index)
                            }
                            disabled={isInspecting}
                            aria-label={
                              `Supprimer ${file.name}`
                            }
                            style={{
                              border: "none",
                              background:
                                "transparent",
                              color: "#B91C1C",
                              fontWeight: 900,
                              fontSize: "14px",
                              cursor: isInspecting
                                ? "not-allowed"
                                : "pointer",
                              padding: "5px",
                              flexShrink: 0,
                            }}
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>

                    <div
                      style={{
                        marginTop: "15px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent:
                          "flex-end",
                        gap: "9px",
                        flexWrap: "wrap",
                      }}
                    >
                      <button
                        type="button"
                        onClick={resetAudit}
                        disabled={isInspecting}
                        style={{
                          border:
                            "1px solid #D6D3D1",
                          borderRadius: "7px",
                          padding: "11px 16px",
                          background: "#FFFFFF",
                          color: "#57534E",
                          fontSize: "11px",
                          fontWeight: 800,
                          cursor: isInspecting
                            ? "not-allowed"
                            : "pointer",
                        }}
                      >
                        Réinitialiser
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          void handleInspectDocuments()
                        }
                        disabled={isInspecting}
                        style={{
                          border: "none",
                          borderRadius: "7px",
                          padding: "11px 19px",
                          background: isInspecting
                            ? "#94A3B8"
                            : (
                                "linear-gradient("
                                + "135deg, "
                                + "#059669, "
                                + "#047857)"
                              ),
                          color: "#FFFFFF",
                          fontSize: "11px",
                          fontWeight: 900,
                          cursor: isInspecting
                            ? "not-allowed"
                            : "pointer",
                          boxShadow: isInspecting
                            ? "none"
                            : (
                                "0 4px 12px "
                                + "rgba(5,150,105,0.18)"
                              ),
                        }}
                      >
                        {isInspecting
                          ? "Analyse OCR en cours..."
                          : "Analyser les documents →"}
                      </button>
                    </div>
                  </div>
                )}
              </div>


              <aside
                style={{
                  flex: "0 0 330px",
                  minWidth: "280px",
                  display: "grid",
                  gap: "13px",
                }}
              >
                <div
                  style={{
                    background: "#FFFFFF",
                    border: "1px solid #E7E5E4",
                    borderRadius: "14px",
                    padding: "20px",
                    boxShadow:
                      "0 7px 24px rgba(28,25,23,0.055)",
                  }}
                >
                  <h2
                    style={{
                      margin: "0 0 7px 0",
                      color: "#14613F",
                      fontFamily:
                        "var(--font-fraunces), Georgia, serif",
                      fontSize: "21px",
                      fontWeight: 700,
                    }}
                  >
                    Avant de commencer
                  </h2>

                  {[
                    {
                      number: "1",
                      title: "Documents lisibles",
                      description:
                        "Assurez-vous que vos pièces sont "
                        + "encore valides.",
                    },
                    {
                      number: "2",
                      title: "Informations cohérentes",
                      description:
                        "Vérifiez que les informations "
                        + "fournies sont complètes et "
                        + "concordantes.",
                    },
                    {
                      number: "3",
                      title: "Résultat indicatif",
                      description:
                        "Les fichiers doivent être lisibles, "
                        + "nets et non endommagés.",
                    },
                  ].map((tip) => (
                    <div
                      key={tip.number}
                      style={{
                        display: "flex",
                        gap: "13px",
                        padding: "14px 0",
                        borderBottom:
                          tip.number === "3"
                            ? "none"
                            : "1px solid #F0ECE8",
                      }}
                    >
                      <span
                        style={{
                          width: "37px",
                          height: "37px",
                          borderRadius: "50%",
                          background: "#FFF7E8",
                          color: "#C77700",
                          display: "inline-flex",
                          alignItems: "center",
                          justifyContent: "center",
                          fontFamily:
                            "var(--font-fraunces), Georgia, serif",
                          fontSize: "17px",
                          fontWeight: 700,
                          flexShrink: 0,
                        }}
                      >
                        {tip.number}
                      </span>

                      <div>
                        <div
                          style={{
                            color: "#292524",
                            fontSize: "12px",
                            fontWeight: 850,
                          }}
                        >
                          {tip.title}
                        </div>

                        <div
                          style={{
                            marginTop: "3px",
                            color: "#78716C",
                            fontSize: "10px",
                            lineHeight: 1.5,
                          }}
                        >
                          {tip.description}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>


                <div
                  style={{
                    background:
                      "linear-gradient(135deg, #FFF8EC, #FFFDF8)",
                    border: "1px solid #F4D8AE",
                    borderRadius: "13px",
                    padding: "17px 19px",
                    display: "none",
                    alignItems: "center",
                    gap: "14px",
                  }}
                >
                  <div
                    style={{
                      width: "42px",
                      height: "42px",
                      borderRadius: "50%",
                      border: "1px solid #E3A93A",
                      color: "#C77700",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "20px",
                      flexShrink: 0,
                    }}
                  >
                    ?
                  </div>

                  <div>
                    <div
                      style={{
                        color: "#5B3B14",
                        fontFamily:
                          "var(--font-fraunces), Georgia, serif",
                        fontSize: "14px",
                        fontWeight: 700,
                      }}
                    >
                      Besoin d’aide ?
                    </div>

                    <div
                      style={{
                        marginTop: "3px",
                        color: "#785A39",
                        fontSize: "10px",
                        lineHeight: 1.5,
                      }}
                    >
                      L’assistant du portail peut vous
                      aider à identifier les pièces
                      à préparer.
                    </div>
                  </div>
                </div>
              </aside>
            </div>


            <div
              style={{
                border: "1px solid #CFE6DB",
                borderRadius: "12px",
                padding: "15px 18px",
                background:
                  "linear-gradient(135deg, #F3FAF6, #FBFDFB)",
                display: "none",
                alignItems: "center",
                gap: "13px",
                flexWrap: "wrap",
              }}
            >
              <span
                style={{
                  width: "37px",
                  height: "37px",
                  borderRadius: "50%",
                  background: "#E7F6EE",
                  color: "#08794F",
                  display: "inline-flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "18px",
                  fontWeight: 900,
                  flexShrink: 0,
                }}
              >
                ✓
              </span>

              <div
                style={{
                  flex: "1 1 400px",
                }}
              >
                <div
                  style={{
                    color: "#14613F",
                    fontSize: "11px",
                    fontWeight: 850,
                  }}
                >
                  Traitement de vos documents
                </div>

                <div
                  style={{
                    marginTop: "2px",
                    color: "#64748B",
                    fontSize: "10px",
                    lineHeight: 1.5,
                  }}
                >
                  Les fichiers sont transmis à l’analyse
                  uniquement lorsque vous lancez la
                  pré-analyse documentaire.
                </div>
              </div>

              <div
                style={{
                  color: "#14613F",
                  fontSize: "10px",
                  fontWeight: 800,
                  whiteSpace: "nowrap",
                }}
              >
                PDF · JPG · JPEG · PNG
              </div>
            </div>
          </section>
        )}

        {stage === "profile"
          && inspection && (
          <form
            onSubmit={handleFinalAudit}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr",
                gap: "22px",
                alignItems: "start",
              }}
            >
              <section
                style={{
                  display: showProfileForm
                    ? "none"
                    : "grid",
                  gap: "18px",
                }}
              >
                <div>
                  <div
                    style={{
                      color: "#A16207",
                      fontSize: "11px",
                      fontWeight: 900,
                      letterSpacing: "0.16em",
                      textTransform: "uppercase",
                      marginBottom: "7px",
                    }}
                  >
                    Résultat de la pré-analyse
                  </div>

                  <h2
                    style={{
                      margin: 0,
                      color: "#1C1917",
                      fontFamily:
                        "var(--font-fraunces), Georgia, serif",
                      fontSize: "clamp(27px, 3vw, 39px)",
                      lineHeight: 1.08,
                      fontWeight: 700,
                      letterSpacing: "-0.025em",
                    }}
                  >
                    Votre dossier nécessite
                    quelques compléments.
                  </h2>

                  <p
                    style={{
                      margin: "8px 0 0 0",
                      color: "#64748B",
                      fontSize: "13px",
                      lineHeight: 1.6,
                    }}
                  >
                    Consultez les éléments identifiés
                    avant de compléter les informations
                    de votre projet.
                  </p>
                </div>


                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    width: "100%",
                    maxWidth: "100%",
                  }}
                >
                  <div
                    style={{
                      flex: 1,
                      minHeight: "46px",
                      borderRadius: "7px",
                      border: "1px solid #059669",
                      background:
                        "linear-gradient(135deg, #F0FDF4, #FFFFFF)",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      gap: "10px",
                      color: "#047857",
                      fontSize: "12px",
                      fontWeight: 800,
                      padding: "0 14px",
                    }}
                  >
                    <span
                      style={{
                        width: "22px",
                        height: "22px",
                        borderRadius: "50%",
                        background: "#047857",
                        color: "#FFFFFF",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "12px",
                        fontWeight: 900,
                      }}
                    >
                      ✓
                    </span>

                    1. Documents analysés
                  </div>

                  <div
                    style={{
                      width: "42px",
                      height: "1px",
                      background: "#CBD5E1",
                      flexShrink: 0,
                    }}
                  />

                  <div
                    style={{
                      flex: 1,
                      minHeight: "46px",
                      borderRadius: "7px",
                      border: "1px solid #B91C1C",
                      background:
                        "linear-gradient(135deg, #FFF7F7, #FFFFFF)",
                      display: "flex",
                      justifyContent: "center",
                      alignItems: "center",
                      gap: "10px",
                      color: "#991B1B",
                      fontSize: "12px",
                      fontWeight: 800,
                      padding: "0 14px",
                    }}
                  >
                    <span
                      style={{
                        width: "22px",
                        height: "22px",
                        borderRadius: "50%",
                        background: "#991B1B",
                        color: "#FFFFFF",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "11px",
                        fontWeight: 900,
                      }}
                    >
                      2
                    </span>

                    2. Informations à compléter
                  </div>
                </div>


                <div
                  style={{
                    display: "flex",
                    gap: "22px",
                    alignItems: "flex-start",
                    flexWrap: "wrap",
                  }}
                >
                  <div
                    style={{
                      flex: "1 1 880px",
                      minWidth: 0,
                      display: "grid",
                      gap: "12px",
                    }}
                  >
                    <div
                      style={{
                        display: "grid",
                        gap: "9px",
                      }}
                    >
                      {inspection.documents.map(
                        (document) => (
                          <div
                            key={document.filename}
                            style={{
                              background: "#FFFFFF",
                              border: "1px solid #E7E5E4",
                              borderRadius: "10px",
                              padding: "13px 15px",
                              boxShadow:
                                "0 3px 14px rgba(28,25,23,0.05)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "space-between",
                              gap: "14px",
                            }}
                          >
                            <div
                              style={{
                                display: "flex",
                                gap: "13px",
                                alignItems: "center",
                                minWidth: 0,
                              }}
                            >
                              <div
                                style={{
                                  width: "38px",
                                  height: "45px",
                                  borderRadius: "6px",
                                  border: "1.5px solid #059669",
                                  color: "#047857",
                                  background: "#F0FDF4",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontSize: "20px",
                                  flexShrink: 0,
                                }}
                              >
                                ▤
                              </div>

                              <div style={{ minWidth: 0 }}>
                                <div
                                  style={{
                                    color: "#292524",
                                    fontSize: "13px",
                                    fontWeight: 900,
                                  }}
                                >
                                  {document.filename}
                                </div>

                                <div
                                  style={{
                                    marginTop: "2px",
                                    color: "#047857",
                                    fontSize: "11px",
                                    fontWeight: 800,
                                  }}
                                >
                                  {document.detected_type}
                                </div>

                                <div
                                  style={{
                                    marginTop: "3px",
                                    color: "#78716C",
                                    fontSize: "10px",
                                  }}
                                >
                                  {document.page_count}
                                  {" "}
                                  page
                                  {document.page_count > 1
                                    ? "s"
                                    : ""}
                                  {" • confiance "}
                                  {Math.round(
                                    document.confidence * 100,
                                  )}
                                  {" %"}
                                </div>
                              </div>
                            </div>

                            <span
                              style={{
                                background: "#ECFDF5",
                                border: "1px solid #BBF7D0",
                                color: "#047857",
                                borderRadius: "5px",
                                padding: "5px 9px",
                                fontSize: "10px",
                                fontWeight: 800,
                                whiteSpace: "nowrap",
                              }}
                            >
                              Analysé
                            </span>
                          </div>
                        ),
                      )}
                    </div>


                    {inspection
                      .provisional_missing_documents
                      .length > 0 && (
                      <div
                        style={{
                          background: "#FFFFFF",
                          border: "1px solid #E7E5E4",
                          borderRadius: "10px",
                          padding: "15px 17px 8px",
                          boxShadow:
                            "0 3px 14px rgba(28,25,23,0.04)",
                        }}
                      >
                        <h3
                          style={{
                            margin: "0 0 8px 0",
                            color: "#7F1D1D",
                            fontFamily:
                              "var(--font-fraunces), Georgia, serif",
                            fontSize: "18px",
                            fontWeight: 700,
                          }}
                        >
                          Pièces à ajouter
                        </h3>

                        {inspection
                          .provisional_missing_documents
                          .map((item) => (
                            <div
                              key={item.code}
                              style={{
                                minHeight: "38px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent:
                                  "space-between",
                                gap: "12px",
                                borderBottom:
                                  "1px solid #F1F5F9",
                                padding: "5px 0",
                              }}
                            >
                              <div
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "10px",
                                  minWidth: 0,
                                }}
                              >
                                <span
                                  style={{
                                    color: "#B91C1C",
                                    fontSize: "15px",
                                  }}
                                >
                                  ▧
                                </span>

                                <span
                                  style={{
                                    color: "#292524",
                                    fontSize: "11px",
                                    fontWeight: 700,
                                    lineHeight: 1.4,
                                  }}
                                >
                                  {item.label}
                                </span>
                              </div>

                              <span
                                style={{
                                  flexShrink: 0,
                                  padding: "4px 8px",
                                  borderRadius: "5px",
                                  background: "#FEF2F2",
                                  border:
                                    "1px solid #FECACA",
                                  color: "#991B1B",
                                  fontSize: "9px",
                                  fontWeight: 800,
                                  whiteSpace: "nowrap",
                                }}
                              >
                                À ajouter au dossier
                              </span>
                            </div>
                          ))}
                      </div>
                    )}


                    {inspection
                      .documents_to_determine
                      .length > 0 && (
                      <div
                        style={{
                          background:
                            "linear-gradient(135deg, #EFF6FF, #F8FBFF)",
                          border: "1px solid #BFDBFE",
                          borderRadius: "10px",
                          padding: "14px 17px",
                          boxShadow:
                            "0 3px 14px rgba(30,64,175,0.04)",
                        }}
                      >
                        <h3
                          style={{
                            margin: "0 0 9px 0",
                            color: "#1D4ED8",
                            fontFamily:
                              "var(--font-fraunces), Georgia, serif",
                            fontSize: "17px",
                            fontWeight: 700,
                          }}
                        >
                          À confirmer selon votre projet
                        </h3>

                        <div
                          style={{
                            display: "grid",
                            gap: "7px",
                          }}
                        >
                          {inspection
                            .documents_to_determine
                            .slice(0, 3)
                            .map((item) => (
                              <div
                                key={item.code}
                                style={{
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "10px",
                                  color: "#334155",
                                  fontSize: "11px",
                                  fontWeight: 650,
                                }}
                              >
                                <span
                                  style={{
                                    color: "#2563EB",
                                    fontSize: "14px",
                                  }}
                                >
                                  ▧
                                </span>

                                {item.label}
                              </div>
                            ))}
                        </div>

                        <details
                          style={{
                            marginTop: "9px",
                          }}
                        >
                          <summary
                            style={{
                              color: "#1D4ED8",
                              fontSize: "11px",
                              fontWeight: 800,
                              cursor: "pointer",
                              textDecoration:
                                "underline",
                            }}
                          >
                            Voir les{" "}
                            {
                              inspection
                                .documents_to_determine
                                .length
                            }{" "}
                            éléments à confirmer
                          </summary>

                          <div
                            style={{
                              marginTop: "10px",
                              display: "grid",
                              gap: "8px",
                            }}
                          >
                            {inspection
                              .documents_to_determine
                              .map((item) => (
                                <div
                                  key={item.code}
                                  style={{
                                    background:
                                      "rgba(255,255,255,0.7)",
                                    border:
                                      "1px solid #DBEAFE",
                                    borderRadius: "7px",
                                    padding: "9px 10px",
                                  }}
                                >
                                  <div
                                    style={{
                                      color: "#1E3A8A",
                                      fontSize: "10px",
                                      fontWeight: 800,
                                    }}
                                  >
                                    {item.label}
                                  </div>

                                  <div
                                    style={{
                                      color: "#64748B",
                                      fontSize: "9px",
                                      lineHeight: 1.45,
                                      marginTop: "2px",
                                    }}
                                  >
                                    {item.reason}
                                  </div>
                                </div>
                              ))}
                          </div>
                        </details>
                      </div>
                    )}
                  </div>


                  <aside
                    style={{
                      flex: "0 0 320px",
                      minWidth: "280px",
                      background: "#FFFFFF",
                      border: "1px solid #E7E5E4",
                      borderRadius: "10px",
                      padding: "16px",
                      boxShadow:
                        "0 5px 20px rgba(28,25,23,0.06)",
                      display: "grid",
                      gap: "13px",
                    }}
                  >
                    <h3
                      style={{
                        margin: 0,
                        color: "#7F1D1D",
                        fontFamily:
                          "var(--font-fraunces), Georgia, serif",
                        fontSize: "18px",
                        fontWeight: 700,
                      }}
                    >
                      Synthèse
                    </h3>


                    <div
                      style={{
                        display: "grid",
                        gap: "10px",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          color: "#292524",
                          fontSize: "11px",
                        }}
                      >
                        <span
                          style={{
                            width: "29px",
                            height: "29px",
                            borderRadius: "50%",
                            background: "#ECFDF5",
                            color: "#047857",
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontWeight: 900,
                          }}
                        >
                          ▤
                        </span>

                        <strong>
                          {inspection.documents.length}
                        </strong>

                        document
                        {inspection.documents.length > 1
                          ? "s"
                          : ""}{" "}
                        analysé
                        {inspection.documents.length > 1
                          ? "s"
                          : ""}
                      </div>

                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          color: "#292524",
                          fontSize: "11px",
                        }}
                      >
                        <span
                          style={{
                            width: "29px",
                            height: "29px",
                            borderRadius: "50%",
                            background: "#FEF2F2",
                            color: "#B91C1C",
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontWeight: 900,
                          }}
                        >
                          ▧
                        </span>

                        <strong>
                          {
                            inspection
                              .provisional_missing_documents
                              .length
                          }
                        </strong>

                        pièces à ajouter
                      </div>

                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "10px",
                          color: "#292524",
                          fontSize: "11px",
                        }}
                      >
                        <span
                          style={{
                            width: "29px",
                            height: "29px",
                            borderRadius: "50%",
                            background: "#EFF6FF",
                            color: "#2563EB",
                            display: "inline-flex",
                            alignItems: "center",
                            justifyContent: "center",
                            fontWeight: 900,
                          }}
                        >
                          ≡
                        </span>

                        <strong>
                          {
                            inspection
                              .documents_to_determine
                              .length
                          }
                        </strong>

                        éléments à confirmer
                      </div>
                    </div>


                    {inspection.missing_fields.length > 0 && (
                      <div
                        style={{
                          background: "#FFFBEB",
                          border: "1px solid #FDE68A",
                          borderRadius: "8px",
                          padding: "11px",
                        }}
                      >
                        <div
                          style={{
                            color: "#92400E",
                            fontSize: "11px",
                            fontWeight: 900,
                            marginBottom: "8px",
                          }}
                        >
                          Informations manquantes
                        </div>

                        <div
                          style={{
                            display: "flex",
                            gap: "5px",
                            flexWrap: "wrap",
                          }}
                        >
                          {inspection.missing_fields.map(
                            (field) => (
                              <span
                                key={field}
                                style={{
                                  padding:
                                    "5px 8px",
                                  borderRadius:
                                    "9999px",
                                  background:
                                    "#FEF3C7",
                                  color: "#92400E",
                                  fontSize: "9px",
                                  fontWeight: 800,
                                }}
                              >
                                {missingFieldLabels[
                                  field
                                ] ?? field}
                              </span>
                            ),
                          )}
                        </div>
                      </div>
                    )}


                    <button
                      type="button"
                      onClick={() => {
                        setShowProfileForm(true);

                        window.setTimeout(() => {
                          document
                            .getElementById(
                              "project-profile-form",
                            )
                            ?.scrollIntoView({
                              behavior: "smooth",
                              block: "start",
                            });
                        }, 60);
                      }}
                      style={{
                        width: "100%",
                        border: "none",
                        borderRadius: "6px",
                        padding: "12px 14px",
                        background:
                          "linear-gradient(135deg, #059669, #047857)",
                        color: "#FFFFFF",
                        fontSize: "11px",
                        fontWeight: 900,
                        cursor: "pointer",
                        boxShadow:
                          "0 4px 12px rgba(5,150,105,0.18)",
                      }}
                    >
                      Compléter les informations →
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setStage("documents")
                      }
                      style={{
                        width: "100%",
                        border: "1px solid #059669",
                        borderRadius: "6px",
                        padding: "11px 14px",
                        background: "#FFFFFF",
                        color: "#047857",
                        fontSize: "11px",
                        fontWeight: 850,
                        cursor: "pointer",
                      }}
                    >
                      Modifier mes documents
                    </button>
                  </aside>
                </div>
              </section>

              <section
                id="project-profile-form"
                className="document-profile-form"
                style={{
                  ...cardStyle,
                  display: showProfileForm
                    ? "block"
                    : "none",
                }}
              >
                <button
                  type="button"
                  onClick={() => {
                    setShowProfileForm(false);

                    window.setTimeout(() => {
                      window.scrollTo({
                        top: 0,
                        behavior: "smooth",
                      });
                    }, 50);
                  }}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: "7px",
                    width: "fit-content",
                    border: "1px solid #D8B4B4",
                    borderRadius: "8px",
                    background: "#FFF7F7",
                    color: "#8B0000",
                    padding: "9px 14px",
                    marginBottom: "20px",
                    fontSize: "12px",
                    fontWeight: 800,
                    cursor: "pointer",
                    boxShadow:
                      "0 2px 8px rgba(139,0,0,0.06)",
                  }}
                >
                  ← Retour à la pré-analyse
                </button>

                <div
                  style={{
                    marginBottom: "22px",
                  }}
                >
                  <h2
                    style={{
                      margin: "0 0 6px 0",
                      fontSize: "20px",
                      fontWeight: 900,
                    }}
                  >
                    Vérifiez et complétez
                    les informations
                  </h2>

                  <p
                    style={{
                      margin: 0,
                      fontSize: "13px",
                      lineHeight: 1.6,
                      color: "#64748B",
                    }}
                  >
                    Les données détectées sont
                    préremplies. Corrigez-les
                    si nécessaire et complétez
                    uniquement les champs
                    manquants.
                  </p>
                </div>

                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns:
                      "repeat(2, minmax(0, 1fr))",
                    gap: "16px",
                  }}
                >
                  <div
                    style={{
                      gridColumn: "1 / -1",
                    }}
                  >
                    <label style={labelStyle}>
                      Nom du projet
                      {renderDetectionBadge("project_name")}
                    </label>

                    <input
                      style={inputStyle}
                      value={
                        profile.project_name ?? ""
                      }
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          project_name:
                            event.target.value,
                        }))
                      }
                      placeholder={
                        "Ex. Unité de production "
                        + "de glace"
                      }
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Porteur du projet
                      {renderDetectionBadge("promoter_name")}
                    </label>

                    <input
                      style={inputStyle}
                      value={
                        profile.promoter_name ?? ""
                      }
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          promoter_name:
                            event.target.value,
                        }))
                      }
                      placeholder={
                        "Nom de l’investisseur "
                        + "ou de la société"
                      }
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Forme juridique
                      {renderDetectionBadge("legal_form")}
                    </label>

                    <input
                      style={inputStyle}
                      value={
                        profile.legal_form ?? ""
                      }
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          legal_form:
                            event.target.value,
                        }))
                      }
                      placeholder={
                        "Ex. SARL, SARL AU, SA..."
                      }
                    />
                  </div>

                  <div
                    style={{
                      gridColumn: "1 / -1",
                    }}
                  >
                    <label
                    style={{
                      ...labelStyle,
                      display: "block",
                    }}
                  >
                    CIN / Passeport du porteur ou représentant{" "}
                    <span
                      style={{
                        display: "inline-block",
                        marginLeft: "6px",
                        padding: "2px 7px",
                        borderRadius: "9999px",
                        background: "#FEF3C7",
                        color: "#A16207",
                        fontSize: "10px",
                        fontWeight: 800,
                      }}
                    >
                      À compléter
                    </span>

                    <input
                      type="text"
                      value={
                        profile.identity_document_number
                        ?? ""
                      }
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          identity_document_number:
                            event.target.value
                              .toUpperCase(),
                        }))
                      }
                      placeholder="Ex. AB123456"
                      maxLength={50}
                      autoComplete="off"
                      style={{
                        ...inputStyle,
                        marginTop: "7px",
                      }}
                    />
                  </label>

                  <label style={labelStyle}>
                      Secteur d’activité *
                      {renderDetectionBadge("sector")}
                    </label>

                    <input
                      required
                      style={inputStyle}
                      value={profile.sector}
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          sector:
                            event.target.value,
                        }))
                      }
                      placeholder={
                        "Ex. Agroalimentaire, "
                        + "Tourisme, Industrie..."
                      }
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Investissement en MAD *
                      {renderDetectionBadge("investment_amount_mad")}
                    </label>

                    <input
                      required
                      type="number"
                      min="1"
                      style={inputStyle}
                      value={
                        profile
                          .investment_amount_mad
                        || ""
                      }
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          investment_amount_mad:
                            Number(
                              event.target.value,
                            ),
                        }))
                      }
                      placeholder="Ex. 5000000"
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Emplois prévus
                      {renderDetectionBadge("planned_jobs")}
                    </label>

                    <input
                      type="number"
                      min="0"
                      style={inputStyle}
                      value={
                        profile.planned_jobs
                        || ""
                      }
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          planned_jobs:
                            Number(
                              event.target.value,
                            ),
                        }))
                      }
                      placeholder="Ex. 25"
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Région *
                      {renderDetectionBadge("region")}
                    </label>

                    <input
                      required
                      style={inputStyle}
                      value={profile.region}
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          region:
                            event.target.value,
                        }))
                      }
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Province *
                      {renderDetectionBadge("province")}
                    </label>

                    <input
                      required
                      style={inputStyle}
                      value={profile.province}
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          province:
                            event.target.value,
                        }))
                      }
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Commune *
                      {renderDetectionBadge("commune")}
                    </label>

                    <input
                      required
                      style={inputStyle}
                      value={profile.commune}
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          commune:
                            event.target.value,
                        }))
                      }
                    />
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Type d’investisseur
                      {renderDetectionBadge("investor_type")}
                    </label>

                    <select
                      style={inputStyle}
                      value={
                        profile.investor_type
                      }
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          investor_type:
                            event.target.value as ProjectProfile["investor_type"],
                        }))
                      }
                    >
                      <option
                        value="societe_en_creation"
                      >
                        Société en création
                      </option>

                      <option
                        value="societe_existante"
                      >
                        Société existante
                      </option>

                      <option
                        value="personne_physique"
                      >
                        Personne physique
                      </option>
                    </select>
                  </div>

                  <div>
                    <label style={labelStyle}>
                      Situation foncière
                      {renderDetectionBadge("land_status")}
                    </label>

                    <select
                      style={inputStyle}
                      value={profile.land_status}
                      onChange={(event) =>
                        setProfile((current) => ({
                          ...current,
                          land_status:
                            event.target.value as ProjectProfile["land_status"],
                        }))
                      }
                    >
                      <option value="non_identifie">
                        Non identifiée
                      </option>

                      <option value="proprietaire">
                        Propriétaire
                      </option>

                      <option value="locataire">
                        Locataire
                      </option>

                      <option
                        value="demande_attribution"
                      >
                        Demande d’attribution
                      </option>
                    </select>
                  </div>

                  <div
                    style={{
                      gridColumn: "1 / -1",
                    }}
                  >
                    <label style={labelStyle}>
                      Nature des travaux
                      {renderDetectionBadge("works")}
                    </label>

                    <div
                      style={{
                        display: "flex",
                        gap: "8px",
                        flexWrap: "wrap",
                      }}
                    >
                      {workOptions.map(
                        (option) => {
                          const selected =
                            profile.works.includes(
                              option.value,
                            );

                          return (
                            <button
                              key={option.value}
                              type="button"
                              onClick={() =>
                                selectWork(
                                  option.value,
                                )
                              }
                              style={{
                                padding:
                                  "7px 13px",
                                borderRadius:
                                  "9999px",
                                border: selected
                                  ? (
                                      "1.5px "
                                      + "solid "
                                      + "#8B0000"
                                    )
                                  : (
                                      "1px solid "
                                      + "#CBD5E1"
                                    ),
                                background: selected
                                  ? "#FEF2F2"
                                  : "#FFFFFF",
                                color: selected
                                  ? "#8B0000"
                                  : "#475569",
                                fontSize: "12px",
                                fontWeight:
                                  selected
                                    ? 800
                                    : 600,
                                cursor: "pointer",
                              }}
                            >
                              {option.label}
                            </button>
                          );
                        },
                      )}
                    </div>
                  </div>

                  <div
                    style={{
                      gridColumn: "1 / -1",
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(2, 1fr)",
                      gap: "10px",
                    }}
                  >
                    {[
                      {
                        key:
                          "requests_incentives",
                        label:
                          "Demande de primes",
                      },
                      {
                        key:
                          "requests_bank_financing",
                        label:
                          "Financement bancaire",
                      },
                      {
                        key:
                          "potential_environmental_impact",
                        label:
                          "Impact environnemental potentiel",
                      },
                      {
                        key:
                          "regulated_activity",
                        label:
                          "Activité réglementée",
                      },
                    ].map((option) => (
                      <label
                        key={option.key}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "8px",
                          padding: "10px",
                          borderRadius: "10px",
                          background: "#F8FAFC",
                          border:
                            "1px solid #E2E8F0",
                          fontSize: "12px",
                          fontWeight: 700,
                          color: "#475569",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={Boolean(
                            profile[
                              option.key as keyof ProjectProfile
                            ],
                          )}
                          onChange={(event) =>
                            setProfile(
                              (current) => ({
                                ...current,
                                [option.key]:
                                  event.target
                                    .checked,
                              }),
                            )
                          }
                        />

                        {option.label}
                      </label>
                    ))}
                  </div>
                </div>

                <div
                  style={{
                    display: "flex",
                    justifyContent:
                      "space-between",
                    gap: "12px",
                    flexWrap: "wrap",
                    marginTop: "26px",
                  }}
                >
                  <button
                    type="button"
                    onClick={() =>
                      setStage("documents")
                    }
                    disabled={isAuditing}
                    style={{
                      border:
                        "1px solid #CBD5E1",
                      borderRadius:
                        "9999px",
                      padding: "12px 20px",
                      background: "#FFFFFF",
                      color: "#475569",
                      fontWeight: 700,
                      cursor: "pointer",
                    }}
                  >
                    ← Modifier les documents
                  </button>

                  <button
                    type="submit"
                    disabled={isAuditing}
                    style={{
                      border: "none",
                      borderRadius:
                        "9999px",
                      padding: "12px 24px",
                      background: isAuditing
                        ? "#CBD5E1"
                        : (
                            "linear-gradient("
                            + "135deg, "
                            + "#008751, "
                            + "#046C42)"
                          ),
                      color: "#FFFFFF",
                      fontWeight: 800,
                      cursor: isAuditing
                        ? "not-allowed"
                        : "pointer",
                    }}
                  >
                    {isAuditing
                      ? "Audit en cours..."
                      : "Lancer l’audit complet →"}
                  </button>
                </div>
              </section>
            </div>
          </form>
        )}


        {stage === "profile"
          && inspection
          && result
          && showProfileForm && (
          <section
            id="audit-complete-actions"
            style={{
              marginTop: "24px",
              border:
                "1px solid #BBF7D0",
              borderRadius: "22px",
              background:
                "linear-gradient("
                + "135deg, #F0FDF4, #FFFFFF)",
              padding: "30px",
              boxShadow:
                "0 12px 35px "
                + "rgba(22, 101, 52, 0.08)",
            }}
          >
            <div
              style={{
                display: "flex",
                gap: "18px",
                alignItems: "flex-start",
                flexWrap: "wrap",
              }}
            >
              <div
                style={{
                  width: "52px",
                  height: "52px",
                  borderRadius: "50%",
                  background: "#DCFCE7",
                  color: "#15803D",
                  display: "grid",
                  placeItems: "center",
                  fontSize: "27px",
                  fontWeight: 900,
                  flexShrink: 0,
                }}
                aria-hidden="true"
              >
                ✓
              </div>

              <div
                style={{
                  flex: "1 1 420px",
                }}
              >
                <div
                  style={{
                    color: "#15803D",
                    fontSize: "11px",
                    fontWeight: 900,
                    letterSpacing: "0.14em",
                    textTransform: "uppercase",
                    marginBottom: "7px",
                  }}
                >
                  Audit terminé
                </div>

                <h2
                  style={{
                    margin: "0 0 8px 0",
                    fontFamily:
                      "var(--font-fraunces), Georgia, serif",
                    fontSize: "28px",
                    lineHeight: 1.15,
                    color: "#1C1917",
                  }}
                >
                  Analyse du dossier terminée
                </h2>

                <p
                  style={{
                    margin: 0,
                    color: "#57534E",
                    fontSize: "14px",
                    lineHeight: 1.7,
                    maxWidth: "650px",
                  }}
                >
                  L’audit complet a été réalisé avec
                  succès. Vous pouvez télécharger le
                  rapport PDF ou discuter de cette
                  analyse avec l’assistant.
                </p>

                <div
                  style={{
                    marginTop: "24px",
                    display: "flex",
                    gap: "12px",
                    flexWrap: "wrap",
                  }}
                >
                  <button
                    type="button"
                    onClick={() =>
                      void handleDownloadReport()
                    }
                    disabled={
                      isDownloadingReport
                    }
                    style={{
                      border: "none",
                      borderRadius: "9999px",
                      padding: "13px 22px",
                      background:
                        isDownloadingReport
                          ? "#94A3B8"
                          : "#15803D",
                      color: "#FFFFFF",
                      fontWeight: 800,
                      fontSize: "13px",
                      cursor:
                        isDownloadingReport
                          ? "not-allowed"
                          : "pointer",
                    }}
                  >
                    {isDownloadingReport
                      ? "Génération du PDF..."
                      : "↓ Télécharger le rapport PDF"}
                  </button>

                  {onDiscussAnalysis && (
                    <button
                      type="button"
                      onClick={() =>
                        onDiscussAnalysis(
                          buildDocumentAnalysisContext(
                            result,
                          ),
                          buildDocumentAnalysisIntroduction(
                            result,
                          ),
                          buildDocumentAnalysisQuestions(
                            result,
                          ),
                        )
                      }
                      style={{
                        border: "none",
                        borderRadius: "9999px",
                        padding: "13px 22px",
                        background: "#8B0000",
                        color: "#FFFFFF",
                        fontWeight: 800,
                        fontSize: "13px",
                        cursor: "pointer",
                      }}
                    >
                      Discuter de cette analyse
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setSourceResult(null);
                    setManualClassifications({});
                    setShowProfileForm(false);

                    window.setTimeout(
                      () => {
                        window.scrollTo({
                          top: 0,
                          behavior: "smooth",
                        });
                      },
                      0,
                    );
                  }}
                  style={{
                    marginTop: "16px",
                    border:
                      "1px solid #D6D3D1",
                    borderRadius: "9999px",
                    padding: "10px 18px",
                    background: "#FFFFFF",
                    color: "#44403C",
                    fontWeight: 700,
                    fontSize: "12px",
                    cursor: "pointer",
                  }}
                >
                  ← Retour à la pré-analyse
                </button>
              </div>
            </div>
          </section>
        )}

        {stage === "results"
          && result && (
          <section
            style={{
              display: "grid",
              gap: "22px",
            }}
          >
            <div
              style={{
                background:
                  "linear-gradient("
                  + "135deg, "
                  + "#1A1A1A, "
                  + "#2A2A2A)",
                borderRadius: "20px",
                padding: "28px 32px",
                color: "#FFFFFF",
                display: "flex",
                justifyContent:
                  "space-between",
                alignItems: "center",
                gap: "20px",
                flexWrap: "wrap",
                boxShadow:
                  "0 10px 30px "
                  + "rgba(0,0,0,0.15)",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "11px",
                    color: "#6EE7B7",
                    fontWeight: 900,
                    letterSpacing: "0.08em",
                    textTransform:
                      "uppercase",
                  }}
                >
                  Résultat de l’audit
                </div>

                <h2
                  style={{
                    margin: "5px 0 0 0",
                    fontSize: "25px",
                  }}
                >
                  Score de complétude :
                  {" "}
                  {Math.round(
                    result.audit.summary
                      .completeness_percentage,
                  )}
                  %
                </h2>

                <div
                  style={{
                    marginTop: "7px",
                    fontSize: "13px",
                    color: "#D1D5DB",
                  }}
                >
                  {
                    profile.project_name
                    || "Projet sans nom précisé"
                  }
                  {" — "}
                  {profile.sector}
                </div>
              </div>

              <div
                style={{
                  display: "flex",
                  gap: "22px",
                  textAlign: "center",
                }}
              >
                <div>
                  <strong
                    style={{
                      display: "block",
                      fontSize: "23px",
                      color: "#6EE7B7",
                    }}
                  >
                    {
                      result.audit.summary
                        .submitted_document_count
                    }
                  </strong>

                  <span
                    style={{
                      fontSize: "11px",
                      color: "#CBD5E1",
                    }}
                  >
                    Transmis
                  </span>
                </div>

                <div>
                  <strong
                    style={{
                      display: "block",
                      fontSize: "23px",
                      color: "#FCD34D",
                    }}
                  >
                    {
                      result.audit.summary
                        .present_requirement_count
                    }
                  </strong>

                  <span
                    style={{
                      fontSize: "11px",
                      color: "#CBD5E1",
                    }}
                  >
                    Détectés
                  </span>
                </div>

                <div>
                  <strong
                    style={{
                      display: "block",
                      fontSize: "23px",
                      color: "#FCA5A5",
                    }}
                  >
                    {
                      result.audit.summary
                        .missing_required_count
                    }
                  </strong>

                  <span
                    style={{
                      fontSize: "11px",
                      color: "#CBD5E1",
                    }}
                  >
                    Manquants
                  </span>
                </div>
              </div>
            </div>

            <RequirementList
              title={
                "Pièces détectées par OCR "
                + "— non vérifiées"
              }
              items={presentResults}
              tone="success"
            />

            <RequirementList
              title={
                "Pièces obligatoires "
                + "ou conditionnelles manquantes"
              }
              items={missingResults}
              tone="danger"
            />

            <RequirementList
              title={
                "Pièces recommandées absentes"
              }
              items={recommendedResults}
              tone="warning"
            />

            <div style={cardStyle}>
              <h3
                style={{
                  margin: "0 0 6px 0",
                  fontSize: "17px",
                }}
              >
                Vérification des classifications
              </h3>

              <p
                style={{
                  margin: "0 0 16px 0",
                  fontSize: "12px",
                  color: "#64748B",
                }}
              >
                Vous pouvez corriger manuellement
                le type proposé pour chaque
                document.
              </p>

              <div
                style={{
                  display: "grid",
                  gap: "10px",
                }}
              >
                {result.documents.map(
                  (document) => (
                    <details
                      key={document.filename}
                      style={{
                        padding: "12px",
                        borderRadius: "12px",
                        background: "#F8FAFC",
                        border:
                          "1px solid #E2E8F0",
                      }}
                    >
                      <summary
                        style={{
                          cursor: "pointer",
                          fontSize: "13px",
                          fontWeight: 800,
                          color: "#334155",
                        }}
                      >
                        {document.filename}
                        {" — "}
                        {
                          document.classification
                            .status
                        }
                      </summary>

                      <div
                        style={{
                          marginTop: "12px",
                          display: "grid",
                          gap: "6px",
                        }}
                      >
                        {availableRequirements
                          .map((requirement) => (
                            <label
                              key={
                                requirement.code
                              }
                              style={{
                                display: "flex",
                                alignItems:
                                  "center",
                                gap: "8px",
                                fontSize:
                                  "11px",
                                color:
                                  "#475569",
                              }}
                            >
                              <input
                                type="checkbox"
                                checked={
                                  selectedDocumentCodes(
                                    document,
                                  ).includes(
                                    requirement.code,
                                  )
                                }
                                onChange={(
                                  event,
                                ) =>
                                  toggleDocumentType(
                                    document,
                                    requirement.code,
                                    event.target
                                      .checked,
                                  )
                                }
                              />

                              {requirement.label}
                              {" — "}
                              {levelLabel(
                                requirement.level,
                              )}
                            </label>
                          ))}

                        <button
                          type="button"
                          onClick={() =>
                            restoreAutomaticClassification(
                              document.filename,
                            )
                          }
                          style={{
                            justifySelf: "start",
                            marginTop: "7px",
                            border: "none",
                            background:
                              "transparent",
                            color: "#8B0000",
                            fontSize: "11px",
                            fontWeight: 800,
                            cursor: "pointer",
                          }}
                        >
                          Restaurer la détection
                          automatique
                        </button>
                      </div>
                    </details>
                  ),
                )}
              </div>
            </div>

            {onDiscussAnalysis && (
              <div
                style={{
                  ...cardStyle,
                  background:
                    "linear-gradient("
                    + "135deg, "
                    + "#FFF7ED, "
                    + "#FFFBEB)",
                  border:
                    "1px solid #FCD34D",
                  display: "flex",
                  justifyContent:
                    "space-between",
                  alignItems: "center",
                  gap: "18px",
                  flexWrap: "wrap",
                }}
              >
                <div>
                  <h3
                    style={{
                      margin: "0 0 5px 0",
                      color: "#78350F",
                      fontSize: "17px",
                    }}
                  >
                    Besoin d’une explication ?
                  </h3>

                  <p
                    style={{
                      margin: 0,
                      color: "#92400E",
                      fontSize: "12px",
                    }}
                  >
                    Discutez des pièces
                    présentes, manquantes
                    ou non classées.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() =>
                    void handleDownloadReport()
                  }
                  disabled={isDownloadingReport}
                  style={{
                    border: "none",
                    borderRadius: "9999px",
                    padding: "12px 21px",
                    background:
                      isDownloadingReport
                        ? "#94A3B8"
                        : (
                            "linear-gradient("
                            + "135deg, "
                            + "#008751, "
                            + "#046C42)"
                          ),
                    color: "#FFFFFF",
                    fontWeight: 800,
                    cursor:
                      isDownloadingReport
                        ? "not-allowed"
                        : "pointer",
                    marginLeft: "auto",
                  }}
                >
                  {isDownloadingReport
                    ? "Génération du PDF..."
                    : "Télécharger le rapport PDF"}
                </button>

                <button
                  type="button"
                  onClick={() =>
                    onDiscussAnalysis(
                      buildDocumentAnalysisContext(
                        result,
                      ),
                      buildDocumentAnalysisIntroduction(
                        result,
                      ),
                      buildDocumentAnalysisQuestions(
                        result,
                      ),
                    )
                  }
                  style={{
                    border: "none",
                    borderRadius: "9999px",
                    padding: "12px 21px",
                    background:
                      "linear-gradient("
                      + "135deg, "
                      + "#8B0000, "
                      + "#B91C1C)",
                    color: "#FFFFFF",
                    fontWeight: 800,
                    cursor: "pointer",
                  }}
                >
                  Discuter de cette analyse
                </button>
              </div>
            )}

            <div
              style={{
                display: "flex",
                justifyContent:
                  "space-between",
                gap: "12px",
                flexWrap: "wrap",
              }}
            >
              <button
                type="button"
                onClick={() =>
                  setStage("profile")
                }
                style={{
                  border:
                    "1px solid #CBD5E1",
                  borderRadius: "9999px",
                  padding: "12px 20px",
                  background: "#FFFFFF",
                  color: "#475569",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                ← Modifier les informations
              </button>

              <button
                type="button"
                onClick={resetAudit}
                style={{
                  border: "none",
                  borderRadius: "9999px",
                  padding: "12px 22px",
                  background: "#1F2937",
                  color: "#FFFFFF",
                  fontWeight: 800,
                  cursor: "pointer",
                }}
              >
                Nouvelle analyse
              </button>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
