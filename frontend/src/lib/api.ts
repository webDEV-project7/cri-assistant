
export type ConversationSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
};

export type StoredMessage = {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  model: string | null;
  created_at: string;
};

export type ConversationDetail =
  ConversationSummary & {
    messages: StoredMessage[];
  };

export type SourceReference = {
  title: string;
  authority: string;
  url: string;
  page: number | null;
  legal_reference: string | null;
  bulletin_officiel: string | null;
  distance: number;
};

export type AuthUser = {
  id: string;
  name: string;
  email: string;
  auth_provider: string;
  created_at: string;
  last_login: string | null;
  picture?: string;
};

export type ChatResponse = {
  conversation_id: string;
  model: string;
  response: string;
  sources: SourceReference[];
};

type ApiErrorResponse = {
  detail?: unknown;
};

async function getErrorMessage(
  response: Response,
): Promise<string> {
  try {
    const data =
      (await response.json()) as ApiErrorResponse;

    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // La rÃ©ponse d'erreur n'est pas au format JSON.
  }

  return `Erreur HTTP ${response.status}`;
}

async function apiRequest<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  return (await response.json()) as T;
}

export async function registerUser(
  payload: {
    name: string;
    email: string;
    password: string;
  },
): Promise<AuthUser> {
  return apiRequest<AuthUser>(
    "/api/auth/register",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );
}

export async function loginUser(
  payload: {
    email: string;
    password: string;
  },
): Promise<AuthUser> {
  return apiRequest<AuthUser>(
    "/api/auth/login",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );
}

export async function getCurrentUser():
Promise<AuthUser> {
  return apiRequest<AuthUser>(
    "/api/auth/me",
    {
      method: "GET",
      cache: "no-store",
    },
  );
}

export async function logoutCurrentUser():
Promise<void> {
  await apiRequest<{ ok: boolean }>(
    "/api/auth/logout",
    {
      method: "POST",
    },
  );
}

export async function sendChatMessage(
  message: string,
  conversationId: string | null,
  analysisContext?: string | null,
): Promise<ChatResponse> {
  return apiRequest<ChatResponse>(
    "/api/chat",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        analysis_context:
          analysisContext || null,
      }),
    },
  );
}

export async function getConversations():
Promise<ConversationSummary[]> {
  return apiRequest<ConversationSummary[]>(
    "/api/conversations",
    {
      method: "GET",
      cache: "no-store",
    },
  );
}

export async function getConversation(
  conversationId: string,
): Promise<ConversationDetail> {
  return apiRequest<ConversationDetail>(
    `/api/conversations/${conversationId}`,
    {
      method: "GET",
      cache: "no-store",
    },
  );
}

export async function deleteConversation(
  conversationId: string,
): Promise<void> {
  const response = await fetch(
    `/api/conversations/${conversationId}`,
    {
      method: "DELETE",
      credentials: "include",
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }
}
export type GuelmimOuedNounProvince =
  | "Guelmim"
  | "Tan-Tan"
  | "Sidi Ifni"
  | "Assa-Zag";

export type PrimeCalculationRequest = {
  total_investment_mad: number;
  primable_investment_mad: number;
  stable_jobs: number;
  female_payroll_mad: number;
  total_payroll_mad: number;
  future_business: boolean;
  sustainable_project: boolean;
  local_integration: boolean;
  province: GuelmimOuedNounProvince;
  sector: string | null;
  renewable_energy_production: boolean;
};

export type PrimeDetail = {
  code: string;
  label: string;
  rate: number;
  rate_percent: number;
  calculated_ratio?: number;
  sector?: string;
};

export type PrimeLegalReference = {
  type: string;
  numero: string;
  date?: string;
  description?: string;
  dahir?: string;
};

export type PrimeCalculationResponse = {
  eligible: boolean;
  eligibility_details: Record<string, boolean>;
  total_rate: number;
  total_rate_percent: number;
  total_bonus_mad: number;
  details: PrimeDetail[];
  warnings: string[];
  legal_references: PrimeLegalReference[];
  total_investment_mad: number | null;
  primable_investment_mad: number | null;
  stable_jobs: number | null;
  employment_ratio: number | null;
  gender_ratio: number | null;
  raw_rate: number | null;
  raw_rate_percent: number | null;
  reason: string | null;
};

export async function calculatePrimes(
  payload: PrimeCalculationRequest,
): Promise<PrimeCalculationResponse> {
  return apiRequest<PrimeCalculationResponse>(
    "/api/primes/calculate",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );
}

export type InvestorType =
  | "personne_physique"
  | "societe_existante"
  | "societe_en_creation";

export type LandStatus =
  | "proprietaire"
  | "locataire"
  | "demande_attribution"
  | "non_identifie";

export type WorkType =
  | "aucuns_travaux"
  | "construction"
  | "extension"
  | "modification"
  | "lotissement_morcellement";

export type RequirementLevel =
  | "obligatoire"
  | "conditionnelle"
  | "recommandee";

export type ClassificationStatus =
  | "classe"
  | "ambigu"
  | "non_classe";

export type DocumentPresenceStatus =
  | "presente_non_verifiee"
  | "manquante"
  | "recommandee_absente";

export type ProjectProfile = {
  project_name?: string | null;
  promoter_name?: string | null;
  identity_document_number?: string | null;
  legal_form?: string | null;
  sector: string;
  region: string;
  province: string;
  commune: string;
  investor_type: InvestorType;
  land_status: LandStatus;
  investment_amount_mad: number;
  planned_jobs: number;
  works: WorkType[];
  requests_incentives: boolean;
  requests_bank_financing: boolean;
  potential_environmental_impact: boolean;
  regulated_activity: boolean;
};

export type ClassificationCandidate = {
  requirement_code: string;
  requirement_label: string;
  score: number;
  matched_terms: string[];
};

export type DocumentClassificationResult = {
  filename: string;
  status: ClassificationStatus;
  requirement_code: string | null;
  confidence: number;
  candidates: ClassificationCandidate[];
  explanation: string;
};

export type ProcessedDocumentResponse = {
  filename: string;
  page_count: number;
  classification: DocumentClassificationResult;
};

export type ChecklistRequirement = {
  code: string;
  label: string;
  category: string;
  level: RequirementLevel;
  reason: string;
  authority: string | null;
  source_reference: string | null;
};

export type RequirementAuditResult = {
  requirement: ChecklistRequirement;
  status: DocumentPresenceStatus;
  submitted_files: string[];
};

export type DossierAuditSummary = {
  submitted_document_count: number;
  applicable_requirement_count: number;
  present_requirement_count: number;
  missing_required_count: number;
  missing_conditional_count: number;
  recommended_absent_count: number;
  unclassified_document_count: number;
  unknown_requirement_code_count: number;
  duplicate_requirement_count: number;
  completeness_percentage: number;
};

export type DuplicateSubmission = {
  requirement_code: string;
  filenames: string[];
};

export type DossierAuditReport = {
  project_profile: ProjectProfile;
  results: RequirementAuditResult[];
  summary: DossierAuditSummary;
  unclassified_documents: string[];
  unknown_requirement_codes: string[];
  duplicates: DuplicateSubmission[];
  warning: string;
};

export type InvestmentDossierAuditResponse = {
  documents: ProcessedDocumentResponse[];
  audit: DossierAuditReport;
};

export type InspectedInvestmentDocument = {
  filename: string;
  page_count: number;
  detected_type: string;
  confidence: number;
  text_excerpt: string;
};

export type DetectedProjectProfile = {
  project_name: string | null;
  promoter_name: string | null;
  legal_form: string | null;
  sector: string | null;
  region: string | null;
  province: string | null;
  commune: string | null;
  investor_type: InvestorType | null;
  land_status: LandStatus | null;
  investment_amount_mad: number | null;
  planned_jobs: number | null;
  works: WorkType[];
};

export type ProvisionalDocumentRequirement = {
  code: string;
  label: string;
  category: string;
  reason: string;
};

export type InvestmentDocumentInspectionResponse = {
  documents: InspectedInvestmentDocument[];
  detected_documents: string[];
  provisional_missing_documents:
    ProvisionalDocumentRequirement[];
  documents_to_determine:
    ProvisionalDocumentRequirement[];
  detected_profile: DetectedProjectProfile;
  field_sources: Record<string, string[]>;
  missing_fields: string[];
  warning: string;
};

export async function inspectInvestmentDocuments(
  files: File[],
): Promise<InvestmentDocumentInspectionResponse> {
  const formData = new FormData();

  for (const file of files) {
    formData.append("files", file, file.name);
  }

  return apiRequest<InvestmentDocumentInspectionResponse>(
    "/api/investment-dossiers/inspect",
    {
      method: "POST",
      body: formData,
    },
  );
}


export async function auditInvestmentDossier(
  profile: ProjectProfile,
  files: File[],
): Promise<InvestmentDossierAuditResponse> {
  const formData = new FormData();

  formData.append("profile", JSON.stringify(profile));

  for (const file of files) {
    formData.append("files", file, file.name);
  }

  return apiRequest<InvestmentDossierAuditResponse>(
    "/api/investment-dossiers/audit",
    {
      method: "POST",
      body: formData,
    },
  );
}


export async function downloadInvestmentDossierReport(
  result: InvestmentDossierAuditResponse,
): Promise<string> {
  const response = await fetch(
    "/api/investment-dossiers/report",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(result),
      cache: "no-store",
    },
  );

  if (!response.ok) {
    throw new Error(
      await getErrorMessage(response),
    );
  }

  const pdfBlob = await response.blob();

  if (
    pdfBlob.type
    && pdfBlob.type !== "application/pdf"
  ) {
    throw new Error(
      "Le serveur n’a pas retourné un rapport PDF valide.",
    );
  }

  const disposition =
    response.headers.get(
      "Content-Disposition",
    );

  const filenameMatch =
    disposition?.match(
      /filename="?([^";]+)"?/i,
    );

  const filename =
    filenameMatch?.[1]
    || "rapport_pre_analyse.pdf";

  const objectUrl =
    URL.createObjectURL(pdfBlob);

  const downloadLink =
    document.createElement("a");

  downloadLink.href = objectUrl;
  downloadLink.download = filename;
  downloadLink.style.display = "none";

  document.body.appendChild(
    downloadLink,
  );

  downloadLink.click();
  downloadLink.remove();

  window.setTimeout(
    () => URL.revokeObjectURL(objectUrl),
    1000,
  );

  return filename;
}


export type GoogleAuthConfig = {
  client_id: string;
};

export async function getGoogleAuthConfig():
Promise<GoogleAuthConfig> {
  return apiRequest<GoogleAuthConfig>(
    "/api/auth/google-config",
    {
      method: "GET",
      cache: "no-store",
    },
  );
}

export async function loginWithGoogleCredential(
  credential: string,
): Promise<AuthUser> {
  return apiRequest<AuthUser>(
    "/api/auth/google",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        credential,
      }),
    },
  );
}

export type ProvinceStatistic = {
  province: string;
  dossiers: number;
  projects: number;
  investment_amount_mad: number;
  jobs: number;
  investment_share_percent: number;
};

export type RegionalStatistics = {
  has_data: boolean;
  year: number | null;
  dossiers: number;
  projects: number;
  investment_amount_mad: number;
  jobs: number;
  provinces: ProvinceStatistic[];
};

export async function getRegionalStatistics(
  year?: number,
): Promise<RegionalStatistics> {
  const query = year ? `?year=${year}` : "";

  return apiRequest<RegionalStatistics>(
    `/api/public/statistics${query}`,
    {
      method: "GET",
      cache: "no-store",
    },
  );
}



export type TerritorialIndicator = {
  code: string;
  label: string;
  value: number;
  unit: string;
  reference_year: number;
  source_name: string;
  source_url: string | null;
};

export type TerritorialStatistics = {
  has_data: boolean;
  indicators: TerritorialIndicator[];
};

export async function getTerritorialStatistics():
Promise<TerritorialStatistics> {
  return apiRequest<TerritorialStatistics>(
    "/api/public/statistics/territorial",
    {
      method: "GET",
      cache: "no-store",
    },
  );
}


/* =========================================================================
 * TPME - Catalogue réglementaire et simulation
 * ========================================================================= */

export type TpmeProvince = {
  name: string;
  territorial_category: "A" | "B";
};

export type TpmeBranch = {
  name: string;
  priority_activities: string[];
};

export type TpmeSector = {
  name: string;
  tourism_activity: boolean;
  branches: TpmeBranch[];
};

export type TpmeCatalog = {
  version: string;
  region: string;
  source: {
    bulletin_officiel: string;
    arrete_branches: string;
    arrete_activites_prioritaires: string;
    arrete_prime_territoriale: string;
  };
  provinces: TpmeProvince[];
  sectors: TpmeSector[];
};

export type TpmeSimulationRequest = {
  total_investment_mad: number;
  stable_jobs: number;
  equity_financing_mad: number;

  company_age_years: number;
  annual_turnover_mad: number | null;

  studies_trademarks_processes_mad: number;
  private_land_mad: number;
  vehicles_mad: number;
  related_party_investment_mad: number;
  private_land_eligible: boolean;

  owned_over_25_by_large_company: boolean;
  has_public_entity_shareholder: boolean;

  activity_eligible: boolean;
  tourism_activity: boolean;
  priority_activity: boolean;
  territorial_category: "A" | "B" | null;
};

export type TpmePrimableBreakdown = {
  total_investment_mad: number;
  primable_investment_mad: number;

  other_investment_mad: number;

  studies_trademarks_processes_mad: number;
  eligible_studies_mad: number;
  excluded_studies_mad: number;

  private_land_mad: number;
  private_land_eligible: boolean;
  eligible_private_land_mad: number;
  excluded_private_land_mad: number;

  excluded_vehicles_mad: number;
  excluded_related_party_investment_mad: number;
};

export type TpmePrimeDetail = {
  code: string;
  label: string;
  rate: number;
  rate_percent: number;
  calculated_ratio?: number;
  category?: string;
};

export type TpmeLegalReference = {
  type: string;
  numero: string;
  description: string;
};

export type TpmeSimulationResponse = {
  eligible: boolean;
  eligibility_details: Record<string, boolean>;

  total_investment_mad: number;
  primable_investment_mad: number;
  stable_jobs: number;

  employment_ratio: number;
  required_employment_ratio: number;

  equity_financing_mad: number;
  equity_ratio: number;

  new_company: boolean;
  territorial_category: string | null;

  raw_rate: number;
  raw_rate_percent: number;
  total_rate: number;
  total_rate_percent: number;
  total_bonus_mad: number;

  details: TpmePrimeDetail[];
  warnings: string[];
  legal_references: TpmeLegalReference[];

  primable_breakdown: TpmePrimableBreakdown;
};

export async function getTpmeCatalog(): Promise<TpmeCatalog> {
  return apiRequest<TpmeCatalog>(
    "/api/primes/tpme/catalog",
    {
      method: "GET",
    },
  );
}

export async function simulateTpmePrimes(
  payload: TpmeSimulationRequest,
): Promise<TpmeSimulationResponse> {
  return apiRequest<TpmeSimulationResponse>(
    "/api/primes/tpme/simulate",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );
}
