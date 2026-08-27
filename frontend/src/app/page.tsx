"use client";

import DocumentAudit from "@/components/DocumentAudit";
import PrimeCalculator from "@/components/PrimeCalculator";
import WelcomeView from "@/components/WelcomeView";
import ContactView from "@/components/ContactView";
import InvestorServicesView from "@/components/InvestorServicesView";
import ProceduresView from "@/components/ProceduresView";
import GoogleAuthModal, { UserProfile } from "@/components/GoogleAuthModal";
import ConversationHistory from "@/components/ConversationHistory";
import Image from "next/image";
import {
  getCurrentUser,
  logoutCurrentUser,
} from "@/lib/api";
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type {
  FormEvent,
  KeyboardEvent,
} from "react";

import {
  deleteConversation as deleteStoredConversation,
  getConversation,
  getConversations,
  sendChatMessage,
} from "@/lib/api";
import type {
  ConversationSummary,
  SourceReference,
} from "@/lib/api";

type ActiveView =
  | "welcome"
  | "services"
  | "primes"
  | "documents"
  | "procedures"
  | "contact"
  | "assistant"
;

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  model?: string;
  sources?: SourceReference[];
  timestamp?: string;
};

const initialMessages: ChatMessage[] = [
  {
    id: "welcome",
    role: "assistant",
    content:
      "Bonjour, je suis l'assistant du CRI Guelmim-Oued Noun.\nJe peux vous aider à comprendre les démarches, les dispositifs d'aide et les pièces nécessaires à votre projet.\n\nComment puis-je vous accompagner ?",
    model: "Qwen3-8B",
    timestamp: "10:42",
  },
];

const suggestions = [
  "Quelles sont les pièces obligatoires pour obtenir une autorisation de lotir ?",
  "Quelles primes sont disponibles pour un projet dans le secteur agroalimentaire à Guelmim-Oued Noun ?",
  "Comment bénéficier des primes de la Charte de l'Investissement ?",
];

function updateConversationUrl(conversationId: string | null) {
  const newUrl = conversationId
    ? `/?conversation=${encodeURIComponent(conversationId)}`
    : "/";

  window.history.replaceState(null, "", newUrl);
}

function cleanAssistantContent(content: string) {
  return content
    .replace(/\s*\[Source\s+\d+(?:\s*,\s*(?:page|p\.)\s*\d+)?\]/gi, "")
    .replace(/[ \t]+\n/g, "\n")
    .trim();
}

function isLikelyClarification(content: string) {
  const normalizedContent = content.trim().toLowerCase();

  const hasQuestion =
    normalizedContent.includes("?") || normalizedContent.includes("؟");

  const clarificationMarkers = [
    "veuillez préciser",
    "pouvez-vous préciser",
    "quel type",
    "quelle catégorie",
    "dans quelle ville",
    "dans quelle commune",
    "please clarify",
    "which type",
    "what type",
    "which city",
    "يرجى توضيح",
    "المرجو توضيح",
    "ما نوع",
    "أي نوع",
    "في أي مدينة",
    "في أي جماعة",
    "أين يوجد",
  ];

  const hasClarificationMarker = clarificationMarkers.some((marker) =>
    normalizedContent.includes(marker)
  );

  return (
    hasQuestion &&
    (normalizedContent.length <= 1200 || hasClarificationMarker)
  );
}

function OfficialLink({
  content,
  sources,
}: {
  content: string;
  sources: SourceReference[];
}) {
  if (isLikelyClarification(content)) {
    return null;
  }

  const officialSource = sources.find((source) => {
    const candidateUrl = source.url.trim();

    return /^https?:\/\//i.test(candidateUrl);
  });

  if (!officialSource) {
    return null;
  }

  const targetUrl = officialSource.url.trim();
  const containsArabic = /[\u0600-\u06FF]/.test(content);
  const containsEnglish =
    /\b(the|what|which|how|investment|procedure|create|company|business)\b/i.test(
      content
    );

  const linkLabel = containsArabic
    ? "الاطلاع على المصدر الرسمي"
    : containsEnglish
    ? "View the official source"
    : "Consulter la source officielle";

  const targetTitle =
    officialSource.title || linkLabel;

  return (
    <p className="mt-3 text-sm leading-6">
      <a
        className="font-semibold text-emerald-700 underline decoration-emerald-300 underline-offset-4 hover:text-emerald-900"
        href={targetUrl}
        target="_blank"
        rel="noopener noreferrer"
        title={targetTitle}
      >
        {linkLabel}
        <span className="ml-1" aria-hidden="true">
          ↗
        </span>
      </a>
    </p>
  );
}

export default function Home() {
  const [activeView, setActiveView] = useState<ActiveView>("welcome");
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [error, setError] = useState("");
  const [contextNote, setContextNote] = useState<string | null>(null);
  const [historySearch, setHistorySearch] = useState("");
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Auth State
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [authModal, setAuthModal] = useState<{
    isOpen: boolean;
    featureName: string;
    action?: () => void;
  }>({ isOpen: false, featureName: "" });

  useEffect(() => {
    let isCancelled = false;

    getCurrentUser()
      .then((user) => {
        if (!isCancelled) {
          setCurrentUser(user);
        }
      })
      .catch(() => {
        if (!isCancelled) {
          setCurrentUser(null);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  const executeProtectedAction = (featureName: string, action: () => void) => {
    if (currentUser) {
      action();
    } else {
      setAuthModal({
        isOpen: true,
        featureName,
        action,
      });
    }
  };

  const handleAuthSuccess = (user: UserProfile) => {
    setCurrentUser(user);
    const pending = authModal.action;
    setAuthModal({ isOpen: false, featureName: "" });
    if (pending) {
      pending();
    }
  };

  const [
    headerUserMenuOpen,
    setHeaderUserMenuOpen,
  ] = useState(false);

  const headerUserDisplayName = (() => {
    if (!currentUser) {
      return "";
    }

    const profile = currentUser as unknown as Record<
      string,
      unknown
    >;

    const firstName =
      typeof profile.first_name === "string"
        ? profile.first_name.trim()
        : "";

    const lastName =
      typeof profile.last_name === "string"
        ? profile.last_name.trim()
        : "";

    const combinedName = [
      firstName,
      lastName,
    ]
      .filter(Boolean)
      .join(" ");

    if (combinedName) {
      return combinedName;
    }

    const candidates = [
      profile.full_name,
      profile.display_name,
      profile.name,
      profile.username,
      profile.email,
    ];

    for (const candidate of candidates) {
      if (
        typeof candidate === "string" &&
        candidate.trim()
      ) {
        return candidate.trim();
      }
    }

    return "Mon compte";
  })();

  const handleLogout = async () => {
    try {
      await logoutCurrentUser();
    } catch {
      // Intentionally swallowed
    } finally {
      setCurrentUser(null);
      setActiveView("welcome");
      setConversations([]);
      setConversationId(null);
      setMessages(initialMessages);
    }
  };

  const endOfMessagesRef = useRef<HTMLDivElement>(null);
  const [
    documentAnalysisContext,
    setDocumentAnalysisContext,
  ] = useState<string | null>(null);

  const [
    analysisSuggestedQuestions,
    setAnalysisSuggestedQuestions,
  ] = useState<string[]>([]);

  const refreshConversations = useCallback(async () => {
    if (!currentUser) {
      setConversations([]);
      setIsHistoryLoading(false);
      return;
    }

    setIsHistoryLoading(true);

    try {
      const storedConversations =
        await getConversations();

      setConversations(
        storedConversations
      );

    } catch {
      setError(
        "Impossible de charger l’historique des conversations."
      );

    } finally {
      setIsHistoryLoading(false);
    }
  }, [currentUser]);

  useEffect(() => {
    let isCancelled = false;
    const searchParameters = new URLSearchParams(window.location.search);
    const initialConversationId = searchParameters.get("conversation");

    if (!currentUser) {
      return () => {
        isCancelled = true;
      };
    }

    if (!initialConversationId) {
      queueMicrotask(() => {
        if (!isCancelled) {
          setConversationId(null);
          setMessages(initialMessages);
        }
      });
    }

    getConversations()
      .then((storedConversations) => {
        if (isCancelled) return null;
        setConversations(storedConversations);
        if (!initialConversationId) return null;
        return getConversation(initialConversationId);
      })
      .then((storedConversation) => {
        if (isCancelled || !storedConversation) return;
        const storedMessages: ChatMessage[] = storedConversation.messages.map(
          (storedMessage) => ({
            id: storedMessage.id,
            role: storedMessage.role,
            content: storedMessage.content,
            model: storedMessage.model ?? undefined,
          })
        );

        setConversationId(storedConversation.id);
        setMessages(
          storedMessages.length > 0 ? storedMessages : initialMessages
        );
      })
      .catch(() => {
        if (!isCancelled) {
          setError("Impossible de charger la conversation sauvegardée.");
        }
      })
      .finally(() => {
        if (!isCancelled) {
          setIsHistoryLoading(false);
        }
      });

    return () => {
      isCancelled = true;
    };
  }, [currentUser]);

  useEffect(() => {
    if (activeView === "assistant") {
      endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading, activeView]);

  useEffect(() => {
    if (currentUser) {
      return;
    }

    const protectedFeatures: Partial<
      Record<ActiveView, string>
    > = {
      primes: "le Calculateur de Primes",
      documents: "l'Analyse des documents",
      assistant: "l'Assistant IA",
    };

    const featureName =
      protectedFeatures[activeView];

    if (!featureName) {
      return;
    }

    const requestedView = activeView;

    queueMicrotask(() => {
      setActiveView("welcome");

      setAuthModal({
        isOpen: true,
        featureName,
        action: () =>
          setActiveView(requestedView),
      });
    });
  }, [activeView, currentUser]);


  const handleOpenGlobalChat = (contextualMessage?: string) => {
    executeProtectedAction("l'Assistant IA", () => {
      if (contextualMessage) {
        setContextNote(contextualMessage);
      }
    });
  };

  const handleDiscussDocumentAnalysis = (
    analysisContext: string,
    introduction: string,
    suggestedQuestions: string[],
  ) => {
    executeProtectedAction("l'Assistant IA", () => {
      const welcomeMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: introduction,
      };

      setDocumentAnalysisContext(
        analysisContext,
      );

      setAnalysisSuggestedQuestions(
        suggestedQuestions,
      );

      setConversationId(null);
      updateConversationUrl(null);
      setMessages([welcomeMessage]);
      setMessage("");
      setError("");

      setContextNote(
        "Analyse documentaire active : les réponses utilisent le résumé structuré du dernier audit.",
      );
      setActiveView("assistant");
    });
  };

  async function sendMessage(text: string) {
    const cleanMessage = text.trim();
    if (!cleanMessage || isLoading) return;

    const now = new Date();
    const formattedTime = new Intl.DateTimeFormat("fr-MA", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(now);

    setContextNote(
      documentAnalysisContext
        ? "Analyse documentaire active : les réponses utilisent le dernier résultat OCR."
        : null,
    );

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: cleanMessage,
      timestamp: formattedTime,
    };

    setMessages((currentMessages) => [...currentMessages, userMessage]);
    setMessage("");
    setError("");
    setIsLoading(true);

    try {
      const data = await sendChatMessage(
        cleanMessage,
        conversationId,
        documentAnalysisContext,
      );
      setConversationId(data.conversation_id);
      updateConversationUrl(data.conversation_id);

      const assistantNow = new Date();
      const assistantTime = new Intl.DateTimeFormat("fr-MA", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(assistantNow);

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: data.response,
        model: data.model,
        sources: data.sources,
        timestamp: assistantTime,
      };

      setMessages((currentMessages) => [...currentMessages, assistantMessage]);
      await refreshConversations();
    } catch (caughtError: unknown) {
      const errorMessage =
        caughtError instanceof Error
          ? caughtError.message
          : "Une erreur inattendue est survenue.";
      setError(errorMessage);

      const fallbackAssistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "Désolé, je rencontre actuellement une difficulté technique de connexion au serveur. N'hésitez pas à réessayer dans un instant ou à contacter un conseiller du CRI.",
      };
      setMessages((currentMessages) => [...currentMessages, fallbackAssistantMsg]);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleOpenConversation(selectedId: string) {
    if (isLoading) return;
    setDocumentAnalysisContext(null);
    setAnalysisSuggestedQuestions([]);
    setContextNote(null);
    setError("");
    setIsHistoryLoading(true);

    try {
      const storedConversation = await getConversation(selectedId);
      const storedMessages: ChatMessage[] = storedConversation.messages.map(
        (storedMessage) => ({
          id: storedMessage.id,
          role: storedMessage.role,
          content: storedMessage.content,
          model: storedMessage.model ?? undefined,
        })
      );

      setConversationId(storedConversation.id);
      updateConversationUrl(storedConversation.id);
      setMessages(storedMessages.length > 0 ? storedMessages : initialMessages);
    } catch (caughtError: unknown) {
      const errorMessage =
        caughtError instanceof Error
          ? caughtError.message
          : "Impossible de charger la conversation.";
      setError(errorMessage);
    } finally {
      setIsHistoryLoading(false);
    }
  }

  async function handleDeleteConversation(selectedId: string) {
    if (isLoading) return;
    const confirmed = window.confirm("Voulez-vous supprimer cette conversation ?");
    if (!confirmed) return;

    setError("");
    try {
      await deleteStoredConversation(selectedId);
      setConversations((current) =>
        current.filter((c) => c.id !== selectedId)
      );

      if (conversationId === selectedId) {
        setConversationId(null);
        updateConversationUrl(null);
        setMessages(initialMessages);
      }
    } catch (caughtError: unknown) {
      const errorMessage =
        caughtError instanceof Error
          ? caughtError.message
          : "Impossible de supprimer la conversation.";
      setError(errorMessage);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void sendMessage(message);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  function clearConversation() {
    if (isLoading) return;
    setMessages(initialMessages);
    setConversationId(null);
    setContextNote(null);
    setDocumentAnalysisContext(null);
    setAnalysisSuggestedQuestions([]);
    updateConversationUrl(null);
    setMessage("");
    setError("");
  }

  const displayedSuggestions =
    (
      documentAnalysisContext
      && analysisSuggestedQuestions.length > 0
    )
      ? analysisSuggestedQuestions
      : suggestions;

  const getUserInitials = () => {
    if (!currentUser?.name) return "NA";
    const parts = currentUser.name.trim().split(" ");
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    return currentUser.name.substring(0, 2).toUpperCase();
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        fontFamily: "var(--font-inter), sans-serif",
        background: "#FAF6F0",
        color: "#1A1A1A",
      }}
    >
      {/* ── EN-TÊTE INSTITUTIONNEL FIXE DU SITE ── */}
      <header
        style={{
          background: "linear-gradient(135deg, #4A0404 0%, #8B0000 55%, #B91C1C 100%)",
          borderBottom: "1px solid rgba(255,255,255,0.12)",
          position: "sticky",
          top: 0,
          zIndex: 100,
          boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
        }}
      >
        <div
          style={{
            maxWidth: "1400px",
            margin: "0 auto",
            padding: "0 24px",
            height: "80px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "16px",
          }}
        >
          {/* Logo & Identity adapté aux couleurs de l'en-tête */}
          <button
            type="button"
            onClick={() => {
              if (activeView !== "welcome") {
                setActiveView("welcome");
              }
              window.scrollTo({ top: 0, behavior: "smooth" });
            }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              background: "transparent",
              padding: "0",
              borderRadius: "8px",
              border: "none",
              boxShadow: "none",
              cursor: "pointer",
              flexShrink: 0,
              textAlign: "left",
              transition: "transform 0.2s ease, box-shadow 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = "scale(1.02)";
              e.currentTarget.style.boxShadow = "0 6px 18px rgba(0, 0, 0, 0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = "scale(1)";
              e.currentTarget.style.boxShadow = "0 4px 14px rgba(0, 0, 0, 0.2)";
            }}
          >
            <Image
              src="/cri-logo.png"
              alt="CRI Guelmim-Oued Noun"
              width={260}
              height={70}
              style={{
                height: "64px",
                width: "auto",
                objectFit: "contain",
                display: "block",
              }}
              priority
            />
          </button>

          {/* Navigation horizontale unifiée */}
          <nav
            aria-label="Navigation principale"
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              overflowX: "auto",
              padding: "4px 0",
              scrollbarWidth: "none",
            }}
          >
            {[
              {
                label: "Accueil",
                action: () => {
                  if (activeView !== "welcome") {
                    setActiveView("welcome");
                  }
                  window.scrollTo({ top: 0, behavior: "smooth" });
                },
                isActive: activeView === "welcome",
              },
              {
                label: "Parcours investisseur",
                action: () => {
                  if (activeView !== "welcome") {
                    setActiveView("welcome");
                    setTimeout(() => {
                      document.getElementById("parcours-investisseur")?.scrollIntoView({ behavior: "smooth" });
                    }, 120);
                  } else {
                    document.getElementById("parcours-investisseur")?.scrollIntoView({ behavior: "smooth" });
                  }
                },
                isActive: false,
              },
              {
                label: "Analyse des documents",
                action: () =>
                  executeProtectedAction("l'Analyse des documents", () =>
                    setActiveView("documents")
                  ),
                isActive: activeView === "documents",
              },
              {
                label: "Assistant IA",
                action: () =>
                  executeProtectedAction("l'Assistant IA", () =>
                    setActiveView("assistant")
                  ),
                isActive: activeView === "assistant",
              },
              {
                label: "Contact & Localisation",
                action: () => {
                  if (activeView !== "welcome") {
                    setActiveView("welcome");
                    setTimeout(() => {
                      document.getElementById("contact-footer")?.scrollIntoView({ behavior: "smooth" });
                    }, 120);
                  } else {
                    document.getElementById("contact-footer")?.scrollIntoView({ behavior: "smooth" });
                  }
                },
                isActive: false,
              },
            ].map((item) => (
              <button
                key={item.label}
                type="button"
                onClick={item.action}
                style={{
                  padding: "6px 16px",
                  borderRadius: "9999px",
                  border: "none",
                  background: item.isActive
                    ? "#FFFFFF"
                    : "transparent",
                  color: item.isActive ? "#6B0F0F" : "rgba(255,255,255,0.92)",
                  fontSize: "13.5px",
                  fontWeight: item.isActive ? 700 : 500,
                  fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  transition: "all 0.15s ease",
                  flexShrink: 0,
                  boxShadow: item.isActive ? "0 2px 8px rgba(0,0,0,0.15)" : "none",
                }}
                onMouseEnter={(e) => {
                  if (!item.isActive) {
                    e.currentTarget.style.color = "#FFFFFF";
                    e.currentTarget.style.background = "rgba(255,255,255,0.12)";
                  }
                }}
                onMouseLeave={(e) => {
                  if (!item.isActive) {
                    e.currentTarget.style.color = "rgba(255,255,255,0.92)";
                    e.currentTarget.style.background = "transparent";
                  }
                }}
              >
                {item.label}
              </button>
            ))}
          </nav>

          {/* Compte utilisateur */}
          {currentUser && (
            <div
              style={{
                position: "relative",
                flexShrink: 0,
              }}
              onBlur={(event) => {
                const nextTarget =
                  event.relatedTarget as Node | null;

                if (
                  !nextTarget ||
                  !event.currentTarget.contains(
                    nextTarget
                  )
                ) {
                  setHeaderUserMenuOpen(false);
                }
              }}
            >
              <button
                type="button"
                aria-haspopup="menu"
                aria-expanded={
                  headerUserMenuOpen
                }
                onClick={() =>
                  setHeaderUserMenuOpen(
                    (open) => !open
                  )
                }
                style={{
                  minHeight: "40px",
                  maxWidth: "220px",
                  padding: "8px 14px",
                  borderRadius: "9999px",
                  border:
                    "1px solid rgba(255,255,255,0.28)",
                  background:
                    headerUserMenuOpen
                      ? "rgba(255,255,255,0.13)"
                      : "rgba(255,255,255,0.07)",
                  color: "#FFFFFF",
                  fontFamily:
                    "var(--font-outfit), var(--font-inter), sans-serif",
                  fontSize: "13.5px",
                  fontWeight: 600,
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "9px",
                  whiteSpace: "nowrap",
                  transition:
                    "background 0.15s ease, border-color 0.15s ease",
                  outline: "none",
                }}
                onMouseEnter={(event) => {
                  event.currentTarget.style.background =
                    "rgba(255,255,255,0.13)";
                }}
                onMouseLeave={(event) => {
                  if (!headerUserMenuOpen) {
                    event.currentTarget.style.background =
                      "rgba(255,255,255,0.07)";
                  }
                }}
              >
                <svg
                  width="19"
                  height="19"
                  viewBox="0 0 24 24"
                  fill="none"
                  aria-hidden="true"
                  style={{
                    flexShrink: 0,
                  }}
                >
                  <circle
                    cx="12"
                    cy="8"
                    r="4"
                    stroke="currentColor"
                    strokeWidth="1.8"
                  />
                  <path
                    d="M4.5 20c.65-4.05 3.14-6 7.5-6s6.85 1.95 7.5 6"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>

                <span
                  style={{
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {headerUserDisplayName}
                </span>

                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 20 20"
                  fill="none"
                  aria-hidden="true"
                  style={{
                    flexShrink: 0,
                    transform:
                      headerUserMenuOpen
                        ? "rotate(180deg)"
                        : "rotate(0deg)",
                    transition:
                      "transform 0.15s ease",
                  }}
                >
                  <path
                    d="M5 7.5 10 12.5 15 7.5"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>

              {headerUserMenuOpen && (
                <div
                  role="menu"
                  style={{
                    position: "absolute",
                    top: "calc(100% + 10px)",
                    right: 0,
                    width: "190px",
                    padding: "7px",
                    background: "#FFFFFF",
                    border:
                      "1px solid rgba(107,15,15,0.12)",
                    borderRadius: "12px",
                    boxShadow:
                      "0 12px 30px rgba(0,0,0,0.18)",
                    zIndex: 1000,
                  }}
                >
                  <div
                    aria-hidden="true"
                    style={{
                      position: "absolute",
                      top: "-6px",
                      right: "28px",
                      width: "12px",
                      height: "12px",
                      background: "#FFFFFF",
                      borderLeft:
                        "1px solid rgba(107,15,15,0.08)",
                      borderTop:
                        "1px solid rgba(107,15,15,0.08)",
                      transform:
                        "rotate(45deg)",
                    }}
                  />

                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setHeaderUserMenuOpen(
                        false
                      );
                      void handleLogout();
                    }}
                    style={{
                      position: "relative",
                      zIndex: 1,
                      width: "100%",
                      padding: "11px 12px",
                      border: "none",
                      borderRadius: "8px",
                      background:
                        "transparent",
                      color: "#B91C1C",
                      fontFamily:
                        "var(--font-outfit), var(--font-inter), sans-serif",
                      fontSize: "13.5px",
                      fontWeight: 700,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      textAlign: "left",
                    }}
                    onMouseEnter={(event) => {
                      event.currentTarget.style.background =
                        "#FEF2F2";
                    }}
                    onMouseLeave={(event) => {
                      event.currentTarget.style.background =
                        "transparent";
                    }}
                  >
                    <svg
                      width="19"
                      height="19"
                      viewBox="0 0 24 24"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path
                        d="M10 5H6.5A2.5 2.5 0 0 0 4 7.5v9A2.5 2.5 0 0 0 6.5 19H10"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                      />
                      <path
                        d="M14 8l4 4-4 4M18 12H9"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>

                    <span>{"D\u00E9connexion"}</span>
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Bouton principal CTA */}
          <div style={{ flexShrink: 0 }}>
            <button
              type="button"
              onClick={() =>
                executeProtectedAction("le Calculateur de Primes", () =>
                  setActiveView("primes")
                )
              }
              style={{
                padding: "10px 22px",
                borderRadius: "9999px",
                background: "linear-gradient(135deg, #1A6B3C, #0F4A28)",
                border: "1px solid rgba(255,255,255,0.25)",
                color: "#FFFFFF",
                fontSize: "14px",
                fontWeight: 700,
                fontFamily: "var(--font-outfit), var(--font-inter), sans-serif",
                cursor: "pointer",
                boxShadow: "0 4px 14px rgba(26,107,60,0.4)",
                whiteSpace: "nowrap",
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                transition: "transform 0.15s ease, box-shadow 0.15s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = "translateY(-1px)";
                e.currentTarget.style.boxShadow = "0 6px 18px rgba(26,107,60,0.55)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "0 4px 14px rgba(26,107,60,0.4)";
              }}
            >
              <span>⚡</span>
              <span>Simuler mes primes</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1, position: "relative" }}>
        {activeView === "welcome" ? (
          <WelcomeView
            onOpenAssistant={() => handleOpenGlobalChat()}
            onOpenPrimes={() =>
              executeProtectedAction(
                "le Calculateur de Primes",
                () => setActiveView("primes")
              )
            }
            onOpenDocuments={() =>
              executeProtectedAction(
                "l'Analyse des documents",
                () => setActiveView("documents")
              )
            }
          />
        ) : activeView === "services" ? (
          <InvestorServicesView
            onOpenPrimes={() =>
              executeProtectedAction(
                "le Calculateur de Primes",
                () => setActiveView("primes")
              )
            }
            onOpenDocuments={() =>
              executeProtectedAction(
                "l'Analyse des documents",
                () => setActiveView("documents")
              )
            }
            onOpenContact={() => {
              document.getElementById("contact-footer")?.scrollIntoView({ behavior: "smooth" });
            }}
          />
        ) : activeView === "primes" ? (
          <PrimeCalculator />
        ) : activeView === "documents" ? (
          <DocumentAudit
            onDiscussAnalysis={handleDiscussDocumentAnalysis}
          />
        ) : activeView === "procedures" ? (
          <ProceduresView
            onOpenDocuments={() =>
              executeProtectedAction(
                "l'Analyse des documents",
                () => setActiveView("documents")
              )
            }
            onOpenContact={() => {
              document.getElementById("contact-footer")?.scrollIntoView({ behavior: "smooth" });
            }}
          />
        ) : activeView === "contact" ? (
          <ContactView
            onOpenGlobalChat={handleOpenGlobalChat}
            onNavigateToAccueil={() => setActiveView("welcome")}
          />
        ) : (
          /* ── ASSISTANT IA VIEW (SIDEBAR PRO + MESSAGES ALIGNÉS SELON L'IMAGE 2) ── */
          <div
            style={{
              display: "flex",
              height: "calc(100vh - 72px)",
              overflow: "hidden",
              background: "#FAF8F5",
            }}
          >
            {/* ── SIDEBAR GAUCHE ── */}
            <aside
              style={{
                width: isSidebarCollapsed ? "72px" : "310px",
                height: "100%",
                background: "#FFFFFF",
                borderRight: "1px solid #EADECF",
                display: "flex",
                flexDirection: "column",
                transition: "width 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)",
                zIndex: 10,
              }}
            >
              {/* Sidebar Header */}
              <div
                style={{
                  padding: "16px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  borderBottom: "1px solid #F1F5F9",
                }}
              >
                {!isSidebarCollapsed && (
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <div
                      style={{
                        width: "36px",
                        height: "36px",
                        borderRadius: "10px",
                        background: "linear-gradient(135deg, #6B0F0F, #4A0404)",
                        display: "grid",
                        placeItems: "center",
                        flexShrink: 0,
                        boxShadow: "0 2px 8px rgba(107,15,15,0.25)",
                      }}
                    >
                      <Image
                        src="/cri_logo_chat.png"
                        alt="CRI"
                        width={24}
                        height={24}
                        style={{ borderRadius: "50%", objectFit: "cover" }}
                      />
                    </div>
                    <span
                      style={{
                        fontFamily: "var(--font-fraunces), Georgia, serif",
                        fontSize: "14.5px",
                        fontWeight: 700,
                        color: "#1C1610",
                        whiteSpace: "nowrap",
                      }}
                    >
                      CRI Guelmim-Oued Noun
                    </span>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                  title={isSidebarCollapsed ? "Déplier la sidebar" : "Plier la sidebar"}
                  style={{
                    width: "30px",
                    height: "30px",
                    borderRadius: "8px",
                    border: "1px solid #EDE2D4",
                    background: "#FAF6F0",
                    color: "#6B5E4E",
                    display: "grid",
                    placeItems: "center",
                    cursor: "pointer",
                    margin: isSidebarCollapsed ? "0 auto" : "0",
                  }}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    {isSidebarCollapsed ? (
                      <polyline points="9 18 15 12 9 6" />
                    ) : (
                      <polyline points="15 18 9 12 15 6" />
                    )}
                  </svg>
                </button>
              </div>

              {!isSidebarCollapsed && (
                <>
                  {/* Action: Nouvelle discussion */}
                  <div style={{ padding: "14px 16px 10px" }}>
                    <button
                      type="button"
                      onClick={clearConversation}
                      disabled={isLoading}
                      style={{
                        width: "100%",
                        padding: "11px 16px",
                        borderRadius: "8px",
                        background: "linear-gradient(135deg, #6B0F0F, #4A0404)",
                        border: "none",
                        color: "#FFFFFF",
                        fontSize: "14px",
                        fontWeight: 700,
                        fontFamily: "var(--font-outfit), sans-serif",
                        cursor: "pointer",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: "8px",
                        boxShadow: "0 4px 14px rgba(107,15,15,0.25)",
                        transition: "transform 0.15s ease",
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.transform = "translateY(-1px)"; }}
                      onMouseLeave={(e) => { e.currentTarget.style.transform = "translateY(0)"; }}
                    >
                      <span style={{ fontSize: "16px", fontWeight: 800 }}>＋</span>
                      Nouvelle discussion
                    </button>
                  </div>

                  {/* Search Bar */}
                  <div style={{ padding: "0 16px 12px" }}>
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        padding: "8px 12px",
                        borderRadius: "10px",
                        border: "1px solid #EADECF",
                        background: "#FAF8F5",
                      }}
                    >
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#94A3B8" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="11" cy="11" r="8" />
                        <line x1="21" y1="21" x2="16.65" y2="16.65" />
                      </svg>
                      <input
                        type="search"
                        value={historySearch}
                        onChange={(e) => setHistorySearch(e.target.value)}
                        placeholder="Rechercher une conversation..."
                        style={{
                          border: "none",
                          background: "transparent",
                          outline: "none",
                          fontSize: "13px",
                          color: "#1E293B",
                          width: "100%",
                          fontFamily: "inherit",
                        }}
                      />
                    </div>
                  </div>

                  {/* Scrollable Conversation List */}
                  <div style={{ flex: 1, overflowY: "auto", padding: "0 12px 16px" }}>
                    <ConversationHistory
                      conversations={conversations.filter((c) =>
                        c.title
                          .toLowerCase()
                          .includes(historySearch.trim().toLowerCase())
                      )}
                      activeConversationId={conversationId}
                      isLoading={isHistoryLoading}
                      onSelect={handleOpenConversation}
                      onDelete={handleDeleteConversation}
                    />
                  </div>

                  {/* ── FIXE EN BAS: COMPTE UTILISATEUR ── */}
                  <div
                    style={{
                      marginTop: "auto",
                      padding: "12px 14px",
                      borderTop: "1px solid #EADECF",
                      background: "#FAF8F5",
                      position: "sticky",
                      bottom: 0,
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: "10px",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
                        {/* Avatar */}
                        <div
                          style={{
                            width: "36px",
                            height: "36px",
                            borderRadius: "50%",
                            background: "linear-gradient(135deg, #8B0000, #C53030)",
                            color: "#FFFFFF",
                            fontSize: "13px",
                            fontWeight: 800,
                            display: "grid",
                            placeItems: "center",
                            flexShrink: 0,
                            fontFamily: "var(--font-montserrat), sans-serif",
                          }}
                        >
                          {getUserInitials()}
                        </div>

                        {/* Info */}
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div
                            style={{
                              fontSize: "13px",
                              fontWeight: 700,
                              color: "#1A1A1A",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {currentUser?.name || "Nom d'utilisateur"}
                          </div>
                          <div
                            style={{
                              fontSize: "11px",
                              color: "#64748B",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {currentUser?.email || "utilisateur@email.com"}
                          </div>
                        </div>
                      </div>

                      {/* Options icon / menu */}
                      <div style={{ position: "relative" }}>
                        <button
                          type="button"
                          onClick={() => setUserMenuOpen(!userMenuOpen)}
                          title="Options du compte"
                          style={{
                            background: "none",
                            border: "none",
                            color: "#64748B",
                            fontSize: "18px",
                            fontWeight: 700,
                            cursor: "pointer",
                            padding: "4px 6px",
                            borderRadius: "6px",
                          }}
                        >
                          ⋮
                        </button>

                        {userMenuOpen && (
                          <div
                            style={{
                              position: "absolute",
                              bottom: "100%",
                              right: 0,
                              marginBottom: "8px",
                              background: "#FFFFFF",
                              border: "1px solid #EADECF",
                              borderRadius: "10px",
                              boxShadow: "0 10px 25px rgba(0,0,0,0.12)",
                              padding: "6px",
                              width: "160px",
                              zIndex: 100,
                            }}
                          >
                            {currentUser ? (
                              <button
                                type="button"
                                onClick={() => {
                                  setUserMenuOpen(false);
                                  void handleLogout();
                                }}
                                style={{
                                  width: "100%",
                                  padding: "8px 12px",
                                  borderRadius: "6px",
                                  border: "none",
                                  background: "transparent",
                                  color: "#DC2626",
                                  fontSize: "12.5px",
                                  fontWeight: 700,
                                  cursor: "pointer",
                                  textAlign: "left",
                                }}
                              >
                                Déconnexion
                              </button>
                            ) : (
                              <button
                                type="button"
                                onClick={() => {
                                  setUserMenuOpen(false);
                                  setAuthModal({
                                    isOpen: true,
                                    featureName: "l'Assistant IA",
                                  });
                                }}
                                style={{
                                  width: "100%",
                                  padding: "8px 12px",
                                  borderRadius: "6px",
                                  border: "none",
                                  background: "transparent",
                                  color: "#008751",
                                  fontSize: "12.5px",
                                  fontWeight: 700,
                                  cursor: "pointer",
                                  textAlign: "left",
                                }}
                              >
                                Se connecter
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}
            </aside>

            {/* ── ZONE DE CHAT PRINCIPALE (CONFORME À LA DEUXIÈME IMAGE) ── */}
            <div
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                height: "100%",
                background: "#FAF8F5",
                position: "relative",
              }}
            >
              {/* Center Content */}
              <div
                style={{
                  flex: 1,
                  overflowY: "auto",
                  padding: "30px 24px 20px",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                }}
              >
                <div style={{ width: "min(860px, 100%)", display: "flex", flexDirection: "column", gap: "24px" }}>

                  {/* Hero Header on start */}
                  <div
                    style={{
                      textAlign: "center",
                      padding: "20px 0 10px",
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                    }}
                  >
                    <div
                      style={{
                        width: "60px",
                        height: "60px",
                        borderRadius: "16px",
                        background: "linear-gradient(135deg, #6B0F0F, #4A0404)",
                        display: "grid",
                        placeItems: "center",
                        marginBottom: "16px",
                        boxShadow: "0 8px 24px rgba(107,15,15,0.25)",
                      }}
                    >
                      <Image
                        src="/cri_logo_chat.png"
                        alt="CRI"
                        width={40}
                        height={40}
                        style={{ borderRadius: "50%", objectFit: "cover" }}
                      />
                    </div>
                    <h1
                      style={{
                        fontFamily: "var(--font-fraunces), Georgia, serif",
                        fontSize: "clamp(24px, 3.2vw, 34px)",
                        fontWeight: 700,
                        color: "#1C1610",
                        margin: "0 0 10px 0",
                        letterSpacing: "-0.01em",
                      }}
                    >
                      Comment puis-je vous accompagner aujourd’hui ?
                    </h1>
                    <p
                      style={{
                        fontFamily: "var(--font-outfit), sans-serif",
                        fontSize: "15px",
                        color: "#6B5E4E",
                        margin: 0,
                        maxWidth: "600px",
                        lineHeight: 1.6,
                      }}
                    >
                      Posez vos questions sur les démarches, les dispositifs d’aide et les pièces nécessaires à votre projet d’investissement.
                    </p>
                  </div>

                  {/* Context Note if active */}
                  {contextNote && (
                    <div
                      style={{
                        background: "#FFF9E6",
                        border: "1px solid #FDE68A",
                        borderRadius: "8px",
                        padding: "12px 16px",
                        fontSize: "13.5px",
                        color: "#92400E",
                      }}
                    >
                      {contextNote}
                    </div>
                  )}

                  {/* Messages list */}
                  {messages.map((chatMessage) => {
                    const isAssistant = chatMessage.role === "assistant";
                    return (
                      <div
                        key={chatMessage.id}
                        style={{
                          display: "flex",
                          flexDirection: isAssistant ? "column" : "column",
                          alignItems: isAssistant ? "flex-start" : "flex-end",
                          width: "100%",
                        }}
                      >
                        {/* Header info row */}
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            marginBottom: "6px",
                            flexDirection: isAssistant ? "row" : "row-reverse",
                          }}
                        >
                          <div
                            style={{
                              width: "28px",
                              height: "28px",
                              borderRadius: isAssistant ? "8px" : "50%",
                              background: isAssistant
                                ? "linear-gradient(135deg, #8B0000, #C53030)"
                                : "#E6F4EA",
                              border: isAssistant ? "none" : "1px solid #008751",
                              display: "grid",
                              placeItems: "center",
                              color: isAssistant ? "#FFFFFF" : "#008751",
                              fontSize: "12px",
                              fontWeight: 800,
                              fontFamily: "var(--font-montserrat), sans-serif",
                            }}
                          >
                            {isAssistant ? (
                              <Image
                                src="/cri_logo_chat.png"
                                alt="CRI"
                                width={18}
                                height={18}
                                style={{ borderRadius: "50%" }}
                              />
                            ) : (
                              "2"
                            )}
                          </div>

                          {isAssistant && (
                            <div
                              style={{
                                width: "18px",
                                height: "18px",
                                borderRadius: "50%",
                                border: "1px solid #8B0000",
                                color: "#8B0000",
                                fontSize: "11px",
                                fontWeight: 800,
                                display: "grid",
                                placeItems: "center",
                              }}
                            >
                              1
                            </div>
                          )}

                          <span
                            style={{
                              fontSize: "13px",
                              fontWeight: 700,
                              color: "#1E293B",
                            }}
                          >
                            {isAssistant ? "CRI Assistant" : "Vous"}
                          </span>

                          <span style={{ fontSize: "11.5px", color: "#94A3B8" }}>
                            {chatMessage.timestamp || "10:42"}
                          </span>
                        </div>

                        {/* Bubble */}
                        <div
                          style={{
                            maxWidth: "85%",
                            padding: "14px 18px",
                            borderRadius: isAssistant
                              ? "16px 16px 16px 4px"
                              : "16px 16px 4px 16px",
                            background: isAssistant ? "#FFFFFF" : "#E6F4EA",
                            color: isAssistant ? "#1A1A1A" : "#0F5132",
                            border: isAssistant
                              ? "1px solid #EADECF"
                              : "1px solid #C3E6CB",
                            boxShadow: isAssistant
                              ? "0 2px 8px rgba(0,0,0,0.03)"
                              : "none",
                            fontSize: "14.5px",
                            lineHeight: 1.6,
                            whiteSpace: "pre-wrap",
                            wordBreak: "break-word",
                          }}
                        >
                          {isAssistant
                            ? cleanAssistantContent(chatMessage.content)
                            : chatMessage.content}

                          {isAssistant && (
                            <OfficialLink
                              content={chatMessage.content}
                              sources={chatMessage.sources ?? []}
                            />
                          )}

                          {!isAssistant && (
                            <div style={{ textAlign: "right", marginTop: "4px", fontSize: "11px", color: "#008751", fontWeight: 700 }}>
                              ✓✓
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}

                  {/* Suggestions when empty */}
                  {messages.length === 1 && !conversationId && !isLoading && (
                    <div style={{ marginTop: "10px", display: "flex", flexDirection: "column", gap: "10px" }}>
                      {displayedSuggestions.map((suggestion) => (
                        <button
                          key={suggestion}
                          type="button"
                          onClick={() => void sendMessage(suggestion)}
                          style={{
                            padding: "12px 18px",
                            borderRadius: "14px",
                            background: "#FFFFFF",
                            border: "1px solid #EADECF",
                            color: "#1E293B",
                            fontSize: "13.5px",
                            fontWeight: 500,
                            cursor: "pointer",
                            textAlign: "left",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            gap: "12px",
                            boxShadow: "0 2px 6px rgba(0,0,0,0.02)",
                            transition: "all 0.15s ease",
                            fontFamily: "inherit",
                          }}
                          onMouseEnter={(e) => {
                            e.currentTarget.style.borderColor = "#8B0000";
                            e.currentTarget.style.transform = "translateY(-1px)";
                          }}
                          onMouseLeave={(e) => {
                            e.currentTarget.style.borderColor = "#EADECF";
                            e.currentTarget.style.transform = "translateY(0)";
                          }}
                        >
                          <span>{suggestion}</span>
                          <span style={{ color: "#008751", fontSize: "16px", fontWeight: 800 }}>→</span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Typing Indicator */}
                  {isLoading && (
                    <div style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
                      <div
                        style={{
                          width: "28px",
                          height: "28px",
                          borderRadius: "8px",
                          background: "linear-gradient(135deg, #8B0000, #C53030)",
                          display: "grid",
                          placeItems: "center",
                        }}
                      >
                        <Image src="/cri_logo_chat.png" alt="CRI" width={18} height={18} style={{ borderRadius: "50%" }} />
                      </div>
                      <div
                        style={{
                          padding: "12px 18px",
                          borderRadius: "16px 16px 16px 4px",
                          background: "#FFFFFF",
                          border: "1px solid #EADECF",
                          display: "flex",
                          gap: "6px",
                          alignItems: "center",
                        }}
                      >
                        <span style={{ fontSize: "12px", color: "#64748B", fontWeight: 600, marginRight: "4px" }}>CRI Assistant réfléchit</span>
                        {[0, 1, 2].map((i) => (
                          <span
                            key={i}
                            style={{
                              width: "6px",
                              height: "6px",
                              borderRadius: "50%",
                              background: "#8B0000",
                              display: "inline-block",
                              animation: `typingDot 1.2s ${i * 0.2}s infinite ease-in-out`,
                            }}
                          />
                        ))}
                      </div>
                    </div>
                  )}

                  {error && (
                    <div
                      style={{
                        padding: "12px 16px",
                        borderRadius: "8px",
                        background: "#FEF2F2",
                        border: "1px solid #FECACA",
                        color: "#991B1B",
                        fontSize: "13px",
                      }}
                      role="alert"
                    >
                      <strong>Une erreur est survenue : </strong>
                      <span>{error}</span>
                    </div>
                  )}

                  <div ref={endOfMessagesRef} />
                </div>
              </div>

              {/* ── ZONE DE SAISIE (COMPOSER EN BAS) ── */}
              <div
                style={{
                  padding: "14px 24px 20px",
                  background: "transparent",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                }}
              >
                <form
                  onSubmit={handleSubmit}
                  style={{
                    width: "min(860px, 100%)",
                  }}
                >
                  <div
                    style={{
                      background: "#FFFFFF",
                      border: "1px solid #EADECF",
                      borderRadius: "18px",
                      boxShadow: "0 6px 20px rgba(0,0,0,0.04)",
                      padding: "12px 14px 10px 18px",
                      display: "flex",
                      flexDirection: "column",
                      gap: "10px",
                    }}
                  >
                    <textarea
                      id="chat-message"
                      value={message}
                      onChange={(event) => setMessage(event.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder="Écrivez votre question sur l’investissement..."
                      rows={1}
                      maxLength={4000}
                      disabled={isLoading}
                      style={{
                        width: "100%",
                        minHeight: "42px",
                        maxHeight: "120px",
                        resize: "none",
                        border: "none",
                        outline: "none",
                        fontSize: "14.5px",
                        color: "#1E293B",
                        fontFamily: "inherit",
                        lineHeight: 1.5,
                        background: "transparent",
                      }}
                    />

                    {/* Toolbar row */}
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end" }}>
                      {/* Right send button */}
                      <button
                        type="submit"
                        disabled={!message.trim() || isLoading}
                        aria-label="Envoyer"
                        style={{
                          width: "38px",
                          height: "38px",
                          borderRadius: "50%",
                          background: !message.trim() || isLoading ? "#CBD5E1" : "#008751",
                          border: "none",
                          color: "#FFFFFF",
                          display: "grid",
                          placeItems: "center",
                          cursor: !message.trim() || isLoading ? "not-allowed" : "pointer",
                          transition: "background 0.15s ease",
                          boxShadow: !message.trim() || isLoading ? "none" : "0 4px 12px rgba(0,135,81,0.35)",
                        }}
                      >
                        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="22" y1="2" x2="11" y2="13" />
                          <polygon points="22 2 15 22 11 13 2 9 22 2" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  <p
                    style={{
                      margin: "8px 0 0 0",
                      textAlign: "center",
                      fontSize: "11.5px",
                      color: "#94A3B8",
                    }}
                  >
                    Les réponses sont générées par une IA. Vérifiez les informations importantes auprès du CRI.
                  </p>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Google Auth Modal */}
        <GoogleAuthModal
          isOpen={authModal.isOpen}
          targetFeatureName={authModal.featureName}
          onClose={() => setAuthModal({ isOpen: false, featureName: "" })}
          onSuccess={handleAuthSuccess}
        />

        {/* Floating Chatbot Widget */}

        {/* Floating Chatbot Trigger Button (visible when widget is closed) */}
      </main>
    </div>
  );
}
