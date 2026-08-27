import type { ConversationSummary } from "@/lib/api";

type ConversationHistoryProps = {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  isLoading: boolean;
  onSelect: (conversationId: string) => void;
  onDelete: (conversationId: string) => void;
};

type HistoryGroup = "today" | "week" | "older";

function startOfDay(date: Date): Date {
  const result = new Date(date);
  result.setHours(0, 0, 0, 0);
  return result;
}

function historyGroup(dateValue: string): HistoryGroup {
  const date = new Date(dateValue);
  const today = startOfDay(new Date());

  const sevenDaysAgo = new Date(today);
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

  if (date >= today) {
    return "today";
  }
  if (date >= sevenDaysAgo) {
    return "week";
  }
  return "older";
}

function formatConversationDate(dateValue: string): string {
  const date = new Date(dateValue);
  const group = historyGroup(dateValue);

  if (group === "today") {
    return new Intl.DateTimeFormat("fr-MA", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date);
  }

  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);

  if (
    date.getFullYear() === yesterday.getFullYear() &&
    date.getMonth() === yesterday.getMonth() &&
    date.getDate() === yesterday.getDate()
  ) {
    return "Hier";
  }

  return new Intl.DateTimeFormat("fr-MA", {
    day: "2-digit",
    month: "short",
  }).format(date);
}

function HistoryItems({
  conversations,
  activeConversationId,
  onSelect,
  onDelete,
}: {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  onSelect: (conversationId: string) => void;
  onDelete: (conversationId: string) => void;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "3px" }}>
      {conversations.map((conversation) => {
        const isActive = activeConversationId === conversation.id;
        return (
          <div
            key={conversation.id}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderRadius: "10px",
              background: isActive ? "#FDF2F2" : "transparent",
              border: isActive ? "1px solid #FECACA" : "1px solid transparent",
              transition: "all 0.15s ease",
            }}
            onMouseEnter={(e) => {
              if (!isActive) e.currentTarget.style.background = "#F9FAFB";
            }}
            onMouseLeave={(e) => {
              if (!isActive) e.currentTarget.style.background = "transparent";
            }}
          >
            <button
              type="button"
              onClick={() => onSelect(conversation.id)}
              title={conversation.title}
              style={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                gap: "10px",
                padding: "10px 12px",
                background: "none",
                border: "none",
                cursor: "pointer",
                textAlign: "left",
                minWidth: 0,
              }}
            >
              {/* Chat bubble icon */}
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke={isActive ? "#8B0000" : "#64748B"}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                style={{ flexShrink: 0 }}
              >
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>

              <span
                style={{
                  fontSize: "13px",
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? "#8B0000" : "#1E293B",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                  flex: 1,
                }}
              >
                {conversation.title}
              </span>

              <span
                style={{
                  fontSize: "11px",
                  color: isActive ? "#991B1B" : "#94A3B8",
                  flexShrink: 0,
                  marginLeft: "4px",
                }}
              >
                {formatConversationDate(conversation.updated_at)}
              </span>
            </button>

            {/* Delete icon */}
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onDelete(conversation.id);
              }}
              title="Supprimer la conversation"
              style={{
                background: "none",
                border: "none",
                color: "#94A3B8",
                fontSize: "14px",
                padding: "8px 10px",
                cursor: "pointer",
                opacity: isActive ? 1 : 0.6,
                transition: "opacity 0.15s, color 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = "1";
                e.currentTarget.style.color = "#EF4444";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = isActive ? "1" : "0.6";
                e.currentTarget.style.color = "#94A3B8";
              }}
            >
              ✕
            </button>
          </div>
        );
      })}
    </div>
  );
}

export default function ConversationHistory({
  conversations,
  activeConversationId,
  isLoading,
  onSelect,
  onDelete,
}: ConversationHistoryProps) {
  const today = conversations.filter(
    (conversation) => historyGroup(conversation.updated_at) === "today"
  );
  const week = conversations.filter(
    (conversation) => historyGroup(conversation.updated_at) === "week"
  );
  const older = conversations.filter(
    (conversation) => historyGroup(conversation.updated_at) === "older"
  );

  return (
    <section
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        padding: "4px 0",
      }}
      aria-label="Historique des conversations"
    >
      {isLoading && (
        <div style={{ fontSize: "12px", color: "#64748B", padding: "8px 12px" }}>
          Chargement des conversations...
        </div>
      )}

      {!isLoading && conversations.length === 0 && (
        <p style={{ fontSize: "12.5px", color: "#94A3B8", padding: "8px 12px", margin: 0 }}>
          Aucune conversation enregistrée.
        </p>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
        {today.length > 0 && (
          <div>
            <div
              style={{
                fontSize: "11.5px",
                fontWeight: 700,
                color: "#64748B",
                marginBottom: "8px",
                paddingLeft: "4px",
              }}
            >
              Aujourd’hui
            </div>
            <HistoryItems
              conversations={today}
              activeConversationId={activeConversationId}
              onSelect={onSelect}
              onDelete={onDelete}
            />
          </div>
        )}

        {week.length > 0 && (
          <div>
            <div
              style={{
                fontSize: "11.5px",
                fontWeight: 700,
                color: "#64748B",
                marginBottom: "8px",
                paddingLeft: "4px",
              }}
            >
              7 derniers jours
            </div>
            <HistoryItems
              conversations={week}
              activeConversationId={activeConversationId}
              onSelect={onSelect}
              onDelete={onDelete}
            />
          </div>
        )}

        {older.length > 0 && (
          <div>
            <div
              style={{
                fontSize: "11.5px",
                fontWeight: 700,
                color: "#64748B",
                marginBottom: "8px",
                paddingLeft: "4px",
              }}
            >
              Plus ancien
            </div>
            <HistoryItems
              conversations={older}
              activeConversationId={activeConversationId}
              onSelect={onSelect}
              onDelete={onDelete}
            />
          </div>
        )}
      </div>
    </section>
  );
}
