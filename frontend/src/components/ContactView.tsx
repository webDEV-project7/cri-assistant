"use client";

import { useState } from "react";
import type { FormEvent } from "react";

type ContactViewProps = {
  onOpenGlobalChat: (contextualMessage?: string) => void;
  onNavigateToAccueil?: () => void;
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "10px 14px",
  borderRadius: "8px",
  border: "1px solid #CBD5E1",
  fontSize: "14px",
  color: "#0F172A",
  background: "#FFFFFF",
  outline: "none",
  boxSizing: "border-box",
  fontFamily: "inherit",
};

const labelStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "6px",
};

const labelTextStyle: React.CSSProperties = {
  fontSize: "13px",
  fontWeight: 600,
  color: "#374151",
};

export default function ContactView({
  onOpenGlobalChat,
  onNavigateToAccueil,
}: ContactViewProps) {
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    phone: "",
    sector: "",
    message: "",
  });

  const [errors, setErrors] = useState<{
    fullName?: string;
    email?: string;
    message?: string;
  }>({});

  const [submitted, setSubmitted] = useState(false);

  function validateForm() {
    const newErrors: { fullName?: string; email?: string; message?: string } = {};

    if (!formData.fullName.trim()) newErrors.fullName = "Le nom et prénom sont obligatoires.";
    if (!formData.email.trim()) {
      newErrors.email = "L'adresse e-mail est obligatoire.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      newErrors.email = "Veuillez saisir une adresse e-mail valide.";
    }
    if (!formData.message.trim()) newErrors.message = "Le message est obligatoire.";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (validateForm()) setSubmitted(true);
  }

  if (submitted) {
    return (
      <div style={{ minHeight: "100vh", background: "#F8FAFC", fontFamily: "'Inter', sans-serif", display: "flex", flexDirection: "column" }}>
        {/* Blue header */}
        <div style={{ background: "linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #1E40AF 100%)", padding: "40px 32px 48px", color: "#FFF" }}>
          <div style={{ maxWidth: "900px", margin: "0 auto" }}>
            <nav style={{ marginBottom: "20px" }}>
              <button type="button" onClick={onNavigateToAccueil} style={{ background: "none", border: "none", color: "rgba(255,255,255,0.65)", cursor: "pointer", fontSize: "13px", padding: 0 }}>
                Accueil
              </button>
              <span style={{ margin: "0 6px", color: "rgba(255,255,255,0.4)" }}>/</span>
              <span style={{ fontSize: "13px", color: "rgba(255,255,255,0.9)" }}>Contact</span>
            </nav>
            <h1 style={{ fontSize: "clamp(24px,4vw,38px)", fontWeight: 900, margin: 0, letterSpacing: "-0.02em" }}>Contacter un conseiller</h1>
          </div>
        </div>

        {/* Success card */}
        <div style={{ maxWidth: "900px", margin: "-28px auto 40px", padding: "0 24px", width: "100%" }}>
          <div style={{ background: "#FFFFFF", borderRadius: "20px", border: "1px solid #E2E8F0", boxShadow: "0 8px 32px rgba(15,23,42,0.08)", padding: "48px 40px", textAlign: "center" }}>
            <div style={{ fontSize: "56px", marginBottom: "16px" }}>✅</div>
            <h2 style={{ fontSize: "22px", fontWeight: 800, color: "#0F172A", margin: "0 0 10px 0" }}>Votre demande a bien été transmise</h2>
            <p style={{ fontSize: "15px", color: "#64748B", maxWidth: "480px", margin: "0 auto 28px" }}>
              Un conseiller du CRI Guelmim-Oued Noun vous contactera dans les plus brefs délais.
            </p>
            <div style={{ display: "flex", gap: "12px", justifyContent: "center", flexWrap: "wrap" }}>
              <button
                type="button"
                onClick={onNavigateToAccueil}
                style={{ padding: "11px 24px", borderRadius: "9999px", background: "linear-gradient(135deg, #1E3A8A, #0F172A)", border: "none", color: "#FFF", fontWeight: 700, fontSize: "14px", cursor: "pointer", fontFamily: "inherit" }}
              >
                Retour à l’accueil
              </button>
              <button
                type="button"
                onClick={() => onOpenGlobalChat("Bonjour 👋 J'ai soumis une demande de contact. Pouvez-vous m'orienter ?")}
                style={{ padding: "11px 24px", borderRadius: "9999px", background: "linear-gradient(135deg, #F59E0B, #D97706)", border: "none", color: "#FFF", fontWeight: 700, fontSize: "14px", cursor: "pointer", fontFamily: "inherit" }}
              >
                💬 Discuter maintenant
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "#FAF6F0", fontFamily: "var(--font-inter), sans-serif" }}>

      {/* ── OFFICIAL CRI BURGUNDY/RED HEADER ── */}
      <div style={{ background: "linear-gradient(135deg, #4A0404 0%, #8B0000 60%, #B91C1C 100%)", padding: "45px 32px 52px", color: "#FFF" }}>
        <div style={{ maxWidth: "900px", margin: "0 auto" }}>
          <nav style={{ marginBottom: "20px" }}>
            <button
              type="button"
              onClick={onNavigateToAccueil}
              style={{ background: "none", border: "none", color: "rgba(255,255,255,0.75)", cursor: "pointer", fontSize: "13px", padding: 0, fontFamily: "inherit" }}
            >
              Accueil
            </button>
            <span style={{ margin: "0 6px", color: "rgba(255,255,255,0.4)" }}>/</span>
            <span style={{ fontSize: "13px", color: "#FCD34D", fontWeight: 600 }}>Contact</span>
          </nav>

          <h1 style={{ fontFamily: "var(--font-montserrat), sans-serif", fontSize: "clamp(26px,4vw,40px)", fontWeight: 900, margin: "0 0 10px 0", lineHeight: 1.15, letterSpacing: "-0.02em" }}>
            Contacter un conseiller
          </h1>
          <p style={{ fontSize: "15.5px", color: "rgba(255,255,255,0.9)", margin: 0 }}>
            Une équipe régionale à votre écoute pour cadrer et accompagner votre projet.
          </p>
        </div>
      </div>

      {/* ── CONTENT CARD ── */}
      <div style={{ maxWidth: "900px", margin: "-28px auto 40px", padding: "0 24px" }}>
        <div
          style={{
            background: "#FFFFFF",
            borderRadius: "20px",
            border: "1px solid #E2E8F0",
            boxShadow: "0 8px 32px rgba(15,23,42,0.08)",
            overflow: "hidden",
          }}
        >
          {/* Required fields note */}
          <div style={{ padding: "16px 28px", borderBottom: "1px solid #F1F5F9", background: "#FAFBFC" }}>
            <p style={{ margin: 0, fontSize: "13px", color: "#0EA5E9" }}>
              Les champs marqués d’un astérisque sont obligatoires.
            </p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 0 }}>

            {/* LEFT: Form */}
            <form onSubmit={handleSubmit} style={{ padding: "28px", borderRight: "1px solid #F1F5F9" }}>

              {/* Row 1: Name + Email */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
                <label style={labelStyle}>
                  <span style={labelTextStyle}>Nom et prénom <span style={{ color: "#EF4444" }}>*</span></span>
                  <input
                    style={{ ...inputStyle, borderColor: errors.fullName ? "#EF4444" : "#CBD5E1" }}
                    type="text"
                    placeholder=""
                    value={formData.fullName}
                    onChange={(e) => setFormData((d) => ({ ...d, fullName: e.target.value }))}
                  />
                  {errors.fullName && <span style={{ fontSize: "11px", color: "#EF4444" }}>{errors.fullName}</span>}
                </label>

                <label style={labelStyle}>
                  <span style={labelTextStyle}>Adresse e-mail <span style={{ color: "#EF4444" }}>*</span></span>
                  <input
                    style={{ ...inputStyle, borderColor: errors.email ? "#EF4444" : "#CBD5E1" }}
                    type="email"
                    placeholder=""
                    value={formData.email}
                    onChange={(e) => setFormData((d) => ({ ...d, email: e.target.value }))}
                  />
                  {errors.email && <span style={{ fontSize: "11px", color: "#EF4444" }}>{errors.email}</span>}
                </label>
              </div>

              {/* Row 2: Phone + Sector */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "16px" }}>
                <label style={labelStyle}>
                  <span style={labelTextStyle}>Téléphone</span>
                  <input
                    style={inputStyle}
                    type="tel"
                    placeholder=""
                    value={formData.phone}
                    onChange={(e) => setFormData((d) => ({ ...d, phone: e.target.value }))}
                  />
                </label>

                <label style={labelStyle}>
                  <span style={labelTextStyle}>Secteur du projet</span>
                  <select
                    style={inputStyle}
                    value={formData.sector}
                    onChange={(e) => setFormData((d) => ({ ...d, sector: e.target.value }))}
                  >
                    <option value="">Sélectionner...</option>
                    <option value="tourisme">Tourisme et loisirs</option>
                    <option value="industrie">Industrie</option>
                    <option value="agro">Agro-industrie</option>
                    <option value="numerique">Numérique</option>
                    <option value="energie">Énergies renouvelables</option>
                    <option value="logistique">Logistique</option>
                    <option value="autre">Autre</option>
                  </select>
                </label>
              </div>

              {/* Row 3: Message */}
              <label style={{ ...labelStyle, marginBottom: "24px" }}>
                <span style={labelTextStyle}>Votre message <span style={{ color: "#EF4444" }}>*</span></span>
                <textarea
                  style={{
                    ...inputStyle,
                    minHeight: "120px",
                    resize: "vertical",
                    borderColor: errors.message ? "#EF4444" : "#CBD5E1",
                  }}
                  placeholder="Décrivez brièvement votre projet et votre besoin d'accompagnement."
                  value={formData.message}
                  onChange={(e) => setFormData((d) => ({ ...d, message: e.target.value }))}
                />
                {errors.message && <span style={{ fontSize: "11px", color: "#EF4444" }}>{errors.message}</span>}
              </label>

              {/* Actions */}
              <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                <button
                  type="submit"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "12px 24px",
                    borderRadius: "9999px",
                    background: "linear-gradient(135deg, #1E3A8A, #0F172A)",
                    border: "none",
                    color: "#FFF",
                    fontWeight: 700,
                    fontSize: "14px",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    boxShadow: "0 4px 14px rgba(30,58,138,0.35)",
                  }}
                >
                  ✉ Envoyer ma demande
                </button>

                <button
                  type="button"
                  onClick={() => onOpenGlobalChat("Bonjour 👋 Expliquez-nous votre besoin et nous vous orienterons.")}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "12px 24px",
                    borderRadius: "9999px",
                    background: "linear-gradient(135deg, #F59E0B, #D97706)",
                    border: "none",
                    color: "#FFF",
                    fontWeight: 700,
                    fontSize: "14px",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    boxShadow: "0 4px 14px rgba(217,119,6,0.35)",
                  }}
                >
                  💬 Discuter maintenant
                </button>
              </div>
            </form>

            {/* RIGHT: Contact Info */}
            <div style={{ padding: "28px", display: "flex", flexDirection: "column", gap: "20px", background: "#FAFBFC" }}>
              <h3 style={{ margin: "0 0 4px 0", fontSize: "15px", fontWeight: 700, color: "#0F172A" }}>
                Nos coordonnées
              </h3>

              {[
                {
                  icon: "📍",
                  label: "Adresse",
                  value: "Avenue Mohammed V, Guelmim, Région Guelmim-Oued Noun",
                  isLink: false,
                },
                {
                  icon: "📞",
                  label: "Téléphone",
                  value: "Numéro à compléter par le CRI",
                  isPlaceholder: true,
                },
                {
                  icon: "✉️",
                  label: "E-mail",
                  value: "Adresse e-mail à compléter par le CRI",
                  isPlaceholder: true,
                },
              ].map((item) => (
                <div key={item.label} style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
                  <span style={{ fontSize: "18px", flexShrink: 0, marginTop: "1px" }}>{item.icon}</span>
                  <div>
                    <div style={{ fontSize: "11px", fontWeight: 700, color: "#94A3B8", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: "3px" }}>
                      {item.label}
                    </div>
                    <div
                      style={{
                        fontSize: "14px",
                        color: item.isPlaceholder ? "#0EA5E9" : "#374151",
                        fontStyle: item.isPlaceholder ? "italic" : "normal",
                      }}
                    >
                      {item.value}
                    </div>
                  </div>
                </div>
              ))}

              {/* Divider */}
              <div style={{ borderTop: "1px solid #E2E8F0", paddingTop: "20px" }}>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "#64748B", marginBottom: "10px" }}>
                  Horaires d’ouverture
                </div>
                <div style={{ fontSize: "13px", color: "#374151", lineHeight: 1.6 }}>
                  Lundi – Vendredi<br />
                  <strong>08h30 – 16h30</strong>
                </div>
              </div>

              {/* Chat prompt */}
              <div
                style={{
                  background: "linear-gradient(135deg, #EFF6FF, #DBEAFE)",
                  border: "1px solid #BFDBFE",
                  borderRadius: "12px",
                  padding: "14px 16px",
                  marginTop: "auto",
                }}
              >
                <div style={{ fontSize: "13px", fontWeight: 700, color: "#1E3A8A", marginBottom: "4px" }}>
                  🤖 Réponse immédiate
                </div>
                <div style={{ fontSize: "12px", color: "#3B82F6", marginBottom: "10px" }}>
                  L’assistant IA peut répondre à vos questions maintenant.
                </div>
                <button
                  type="button"
                  onClick={() => onOpenGlobalChat()}
                  style={{
                    width: "100%",
                    padding: "9px",
                    borderRadius: "8px",
                    background: "linear-gradient(135deg, #1E3A8A, #0F172A)",
                    border: "none",
                    color: "#FFF",
                    fontWeight: 700,
                    fontSize: "13px",
                    cursor: "pointer",
                    fontFamily: "inherit",
                  }}
                >
                  Discuter avec l’assistant →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
