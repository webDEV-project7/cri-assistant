"use client";

import Image from "next/image";
import { useState } from "react";

type WelcomeViewProps = {
  onOpenAssistant: () => void;
  onOpenPrimes: () => void;
  onOpenDocuments: () => void;
  onOpenContact?: () => void;
};

// ── SERVICES RAPIDES ACCUEIL (Screen 2) ──
const quickServices = [
  {
    number: "01",
    title: "Parcours investisseur",
    description: "Les 5 étapes structurées de l'idée à la concrétisation de votre projet.",
    action: "parcours",
  },
  {
    number: "02",
    title: "Dispositifs & aides",
    description: "Primes de la Charte de l'investissement, soutien TPME et foncier.",
    action: "dispositifs",
  },
  {
    number: "03",
    title: "Simuler vos primes",
    description: "Estimez immédiatement les primes financières éligibles pour votre investissement.",
    action: "primes",
  },
  {
    number: "04",
    title: "Pré-analyser vos documents",
    description: "Vérifiez la conformité et la complétude de votre dossier en un instant.",
    action: "documents",
  },
  {
    number: "05",
    title: "Échanger avec l'Assistant IA",
    description: "Posez toutes vos questions 24/7 sur les procédures et démarches régionales.",
    action: "assistant",
  },
];

// ── ÉTAPES DU PARCOURS INVESTISSEUR (Screen 3) ──
const parcoursSteps = [
  {
    number: "1",
    shortLabel: "Idée",
    stepBadge: "Étape 01",
    title: "Idée & Information territoriale",
    description:
      "Clarifiez votre projet, explorez les secteurs porteurs et accédez aux données clés sur le potentiel de la région Guelmim-Oued Noun.",
    services: [
      "Information économique & sectorielle",
      "Orientation stratégique initiale",
      "Opportunités territoriales prioritaires",
    ],
    tone: "#1A6B3C",
  },
  {
    number: "2",
    shortLabel: "Préparation",
    stepBadge: "Étape 02",
    title: "Préparation & Montage du dossier",
    description:
      "Structurez votre projet d'investissement, préparez les pièces administratives obligatoires et effectuez une pré-analyse documentaire.",
    services: [
      "Checklist des pièces nécessaires",
      "Pré-analyse documentaire intelligente",
      "Cadrage réglementaire & technique",
    ],
    tone: "#B07A00",
  },
  {
    number: "3",
    shortLabel: "Instruction",
    stepBadge: "Étape 03",
    title: "Instruction & Démarches administratives",
    description:
      "Déposez votre dossier pour instruction auprès de la Commission Régionale Unifiée d'Investissement (CRUI) et suivez son avancée.",
    services: [
      "Orientation guichet unique",
      "Instruction coordonnée (CRUI)",
      "Suivi transparent des étapes",
    ],
    tone: "#6B0F0F",
  },
  {
    number: "4",
    shortLabel: "Réalisation",
    stepBadge: "Étape 04",
    title: "Réalisation & Implantation",
    description:
      "Concrétisez votre implantation foncière, mobilisez les partenaires institutionnels et activez vos conventions d'investissement.",
    services: [
      "Accompagnement foncier économique",
      "Mise en relation avec l'écosystème",
      "Facilitation opérationnelle",
    ],
    tone: "#1A6B3C",
  },
  {
    number: "5",
    shortLabel: "Suivi post-investissement",
    stepBadge: "Étape 05",
    title: "Suivi post-investissement & Croissance",
    description:
      "Bénéficiez d'un accompagnement continu pour pérenniser vos activités, créer des emplois durables et étendre vos projets.",
    services: [
      "Aftercare et suivi personnalisé",
      "Médiation et appui au développement",
      "Accompagnement à l'extension",
    ],
    tone: "#B07A00",
  },
];

// ── DISPOSITIFS & AIDES À L'INVESTISSEMENT ──
const dispositifsList = [
  {
    icon: "💎",
    title: "Primes de la Charte de l'Investissement",
    subtitle: "Incitations financières directes",
    description:
      "Bénéficiez du dispositif principal de soutien comprenant des primes communes, territoriales et sectorielles cumulables jusqu'à 30% du montant d'investissement.",
    items: [
      "Prime commune à l'investissement (jusqu'à 30% du montant éligible)",
      "Prime territoriale bonifiée pour les 4 provinces régionales (+10% à +15%)",
      "Prime sectorielle pour les activités durables et à fort impact",
    ],
    tone: "#1A6B3C",
  },
  {
    icon: "🏢",
    title: "Dispositif d'Appui aux TPME",
    subtitle: "Accompagnement ciblé pour les PME & TPE",
    description:
      "Des mesures spécifiques et allégées conçues pour soutenir la création, l'équipement technologique et le développement des TPME de la région.",
    items: [
      "Seuil d'investissement adapté aux petites structures",
      "Primes renforcées pour la création d'emplois locaux stables",
      "Accompagnement méthodologique au démarrage de l'activité",
    ],
    tone: "#B07A00",
  },
  {
    icon: "🗺️",
    title: "Foncier Économique & Zones d'Activités",
    subtitle: "Espaces d'accueil et parcs industriels",
    description:
      "Accès à des assiettes foncières aménagées, connectées et adaptées à vos besoins industriels, logistiques, agricoles, halieutiques ou touristiques.",
    items: [
      "Zones d'activités économiques régionales (Guelmim, Tan-Tan, Sidi Ifni, Assa)",
      "Procédures d'attribution transparentes et sécurisées",
      "Infrastructures modernes et connectivité routière & aéroportuaire",
    ],
    tone: "#6B0F0F",
  },
  {
    icon: "🛡️",
    title: "Accompagnement & Guichet Unique",
    subtitle: "Facilitation et simplification intégrale",
    description:
      "Une équipe dédiée pour vous orienter à chaque étape, simplifier vos formalités et vous connecter directement aux partenaires régionaux.",
    items: [
      "Interlocuteur unique au CRI Guelmim-Oued Noun",
      "Pré-analyse documentaire automatisée par IA",
      "Orientation et médiation administrative personnalisée",
    ],
    tone: "#1A6B3C",
  },
];

// ── ATOUTS STRATÉGIQUES & SECTEURS CLÉS AVEC IMAGES ANIMÉES ──
const strategicSectors = [
  {
    title: "Hub Hydrogène Vert & Énergies Renouvelables",
    category: "Transition Énergétique",
    image: "/sectors/energie-solaire.jpg",
    statBadge: "+3 200 h de soleil / an",
    description:
      "Une position de leader mondial pour l'énergie solaire et éolienne combinée, positionnant Guelmim-Oued Noun comme le futur grand carrefour de l'hydrogène vert et des carburants propres.",
    highlights: ["Solaire & Éolien hybride", "Projets mégawatts", "Export & Industrie verte"],
  },
  {
    title: "Économie Bleue & Industrie Halieutique",
    category: "Ressources Maritimes",
    image: "/sectors/ressources.jpg",
    statBadge: "240 km de côte atlantique",
    description:
      "Façade maritime stratégique avec les ports de Tan-Tan et Sidi Ifni, offrant d'immenses opportunités de transformation des produits de la mer, d'aquaculture durable et de logistique navale.",
    highlights: ["Ports de Tan-Tan & Sidi Ifni", "Transformation halieutique", "Logistique portuaire"],
  },
  {
    title: "Écotourisme, Géoparcs & Oasis Sahariennes",
    category: "Tourisme Durable",
    image: "/sectors/tourisme.jpg",
    statBadge: "4 Provinces uniques",
    description:
      "Des paysages à couper le souffle entre plages atlantiques sauvages (Plage Blanche, Legzira), thermes d'Abaynou et oasis séculaires pour un tourisme écologique haut de gamme.",
    highlights: ["Plage Blanche & Legzira", "Thermalisme d'Abaynou", "Patrimoine oasien"],
  },
];

// ── VALEURS DU CRI ──
const values = [
  {
    title: "Proximité",
    description: "Une équipe régionale à votre écoute au cœur des 4 provinces de Guelmim-Oued Noun.",
  },
  {
    title: "Expertise",
    description: "Une maîtrise approfondie des dispositifs de la nouvelle Charte et des cadres réglementaires.",
  },
  {
    title: "Transparence",
    description: "Des démarches claires, lisibles et des délais d'instruction maîtrisés via la CRUI.",
  },
  {
    title: "Célérité",
    description: "Un traitement accéléré et une réactivité maximale pour concrétiser vos investissements.",
  },
];

export default function WelcomeView({
  onOpenAssistant,
  onOpenPrimes,
  onOpenDocuments,
}: WelcomeViewProps) {
  const [activeStep, setActiveStep] = useState<number>(1);




  const handleQuickAction = (action: string) => {
    if (action === "parcours") {
      document.getElementById("parcours-investisseur")?.scrollIntoView({ behavior: "smooth" });
    } else if (action === "dispositifs") {
      document.getElementById("dispositifs-aides")?.scrollIntoView({ behavior: "smooth" });
    } else if (action === "primes") {
      onOpenPrimes();
    } else if (action === "documents") {
      onOpenDocuments();
    } else if (action === "assistant") {
      onOpenAssistant();
    }
  };

  const currentStepData = parcoursSteps.find((s) => s.number === String(activeStep)) || parcoursSteps[0];

  return (
    <div style={{ backgroundColor: "#F4EDE3", color: "#1C1610", minHeight: "100vh" }}>
      {/* =====================================================
          1. HERO SECTION (Screen 1 - Figma Style)
      ===================================================== */}
      <section
        style={{
          backgroundImage: 'url("/cri1.png")',
          backgroundSize: "cover",
          backgroundPosition: "center center",
          backgroundRepeat: "no-repeat",
          backgroundColor: "#F4EDE3",
          padding: "64px 24px 72px",
          borderBottom: "1px solid #EDE2D4",
          position: "relative",
        }}
      >
        <div
          style={{
            maxWidth: 1360,
            margin: "0 auto",
            display: "grid",
            gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.25fr)",
            gap: 40,
            alignItems: "center",
          }}
        >
          {/* Colonne Gauche: Titres et CTA */}
          <div>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                background: "#FFFFFF",
                border: "1px solid #EDE2D4",
                borderRadius: 999,
                padding: "6px 16px",
                marginBottom: 24,
                boxShadow: "0 2px 6px rgba(0,0,0,0.03)",
              }}
            >
              <span
                style={{
                  fontFamily: "var(--font-dm-mono), monospace",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  letterSpacing: "0.1em",
                  color: "#6B0F0F",
                  textTransform: "uppercase",
                }}
              >
                PORTAIL RÉGIONAL DE L&apos;INVESTISSEMENT
              </span>
            </div>

            <h1
              style={{
                fontFamily: "var(--font-fraunces), Georgia, serif",
                fontSize: "clamp(2.3rem, 4.2vw, 3.5rem)",
                fontWeight: 700,
                lineHeight: 1.12,
                color: "#6B0F0F",
                margin: "0 0 20px",
              }}
            >
              Investir à Guelmim-Oued Noun,
              <br />
              <span style={{ color: "#2c023a" }}>un territoire d&apos;avenir</span>
              <br />
              et d&apos;opportunités durables
            </h1>

            <p
              style={{
                fontFamily: "var(--font-outfit), sans-serif",
                fontSize: "1.08rem",
                fontWeight: 500,
                color: "#1C1610",
                margin: "0 0 10px",
                lineHeight: 1.5,
              }}
            >
              Le Centre Régional d&apos;Investissement vous accompagne de l&apos;idée initiale jusqu&apos;à la concrétisation et l&apos;extension de votre projet.
            </p>

            <p
              style={{
                fontFamily: "var(--font-outfit), sans-serif",
                fontSize: "0.92rem",
                color: "#6B5E4E",
                margin: "0 0 36px",
                lineHeight: 1.6,
              }}
            >
              Accédez à toutes les démarches, simulez vos primes d&apos;investissement de la nouvelle Charte, pré-analysez vos pièces administratives et bénéficiez de l&apos;assistance IA 24/7.
            </p>

            {/* Boutons d'action Hero */}
            <div style={{ display: "flex", gap: 14, flexWrap: "wrap", alignItems: "center" }}>
              <button
                type="button"
                onClick={onOpenPrimes}
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "0.92rem",
                  fontWeight: 700,
                  color: "#FFFFFF",
                  background: "linear-gradient(135deg, #612803, #0F4A28)",
                  border: "1px solid rgba(255,255,255,0.2)",
                  borderRadius: 10,
                  padding: "13px 26px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  boxShadow: "0 4px 14px rgba(26,107,60,0.35)",
                  transition: "transform 0.15s ease, box-shadow 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 6px 20px rgba(26,107,60,0.45)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 4px 14px rgba(26,107,60,0.35)";
                }}
              >
                
                <span>Simuler mes primes</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  document.getElementById("parcours-investisseur")?.scrollIntoView({ behavior: "smooth" });
                }}
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "0.92rem",
                  fontWeight: 600,
                  color: "#6B0F0F",
                  background: "transparent",
                  border: "1.5px solid #6B0F0F",
                  borderRadius: 10,
                  padding: "13px 24px",
                  cursor: "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  transition: "background 0.15s ease, color 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "#6B0F0F";
                  e.currentTarget.style.color = "#ffffff60";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = "transparent";
                  e.currentTarget.style.color = "#6B0F0F";
                }}
              >
                
                <span>Découvrir le parcours investisseur ↓</span>
              </button>
            </div>

            <div
              style={{
                marginTop: 24,
                fontFamily: "var(--font-outfit), sans-serif",
                fontSize: "0.84rem",
                color: "#6B5E4E",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              <span style={{ color: "#1A6B3C", fontWeight: 800 }}>✓</span>
              <span>Assistance IA 24/7 pour toutes vos questions</span>
          </div>
          </div>

          {/* Colonne Droite: CARTE RÉGIONALE DASHBOARD (Conforme à l'image 1 de référence) */}
          <div
            style={{
              background: "#FFFFFF",
              borderRadius: 24,
              border: "1px solid #EDE2D4",
              padding: "24px 24px 20px",
              boxShadow: "0 12px 40px rgba(107,15,15,0.07)",
              display: "flex",
              flexDirection: "column",
              gap: 16,
            }}
          >
            {/* Titre avec souligné doré */}
            <div>
              <div
                style={{
                  fontFamily: "var(--font-fraunces), Georgia, serif",
                  fontSize: "1.3rem",
                  fontWeight: 700,
                  color: "#1C1610",
                  marginBottom: 6,
                }}
              >
                Région Guelmim-Oued Noun
              </div>
              <div style={{ width: 54, height: 3, background: "#B07A00", borderRadius: 2 }} />
            </div>

            {/* Grande Carte Régionale Pleine Largeur avec toutes les villes bien visibles */}
            <div
              style={{
                width: "100%",
                height: 420,
                position: "relative",
                borderRadius: 18,
                overflow: "hidden",
                background: "#FAF6F0",
                border: "1px solid #EDE2D4",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
              className="img-animated"
              title="Carte géographique détaillée de la région Guelmim-Oued Noun"
            >
              <Image
                src="/map-region.jpg"
                alt="Carte de la région Guelmim-Oued Noun (Guelmim, Tan-Tan, Sidi Ifni, Assa-Zag)"
                fill
                style={{
                  objectFit: "contain",
                  padding: "4px",
                  transform: "scale(1.06)",
                  transformOrigin: "center",
                }}
                priority
              />

              {/* Étiquette Océan Atlantique */}
              <div
                style={{
                  position: "absolute",
                  top: 14,
                  left: 14,
                  fontFamily: "var(--font-dm-mono), monospace",
                  fontSize: "0.68rem",
                  fontWeight: 600,
                  letterSpacing: "0.14em",
                  color: "rgba(107,94,78,0.75)",
                  textTransform: "uppercase",
                }}
              >
                OCÉAN ATLANTIQUE
              </div>

              {/* Callout Guelmim-Oued Noun */}
              <div
                style={{
                  position: "absolute",
                  bottom: 14,
                  right: 14,
                  background: "rgba(255,255,255,0.95)",
                  backdropFilter: "blur(6px)",
                  borderRadius: 10,
                  padding: "6px 14px",
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "0.82rem",
                  fontWeight: 700,
                  color: "#6B0F0F",
                  border: "1px solid rgba(107,15,15,0.15)",
                  boxShadow: "0 2px 10px rgba(0,0,0,0.06)",
                }}
              >
                4 Provinces
              </div>
            </div>

            {/* Barre inférieure des 4 indicateurs clés (comme l'image 1 de référence) */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(4, 1fr)",
                gap: 10,
                paddingTop: 16,
                borderTop: "1px solid #EDE2D4",
              }}
            >
              {[
                { icon: "🏗️", label: "Zones d'activités", value: "7", color: "#1A6B3C" },
                { icon: "✈️", label: "Infrastructures clés", value: "Aéroport · Port · Réseau routier", color: "#B07A00" },
                { icon: "🌬️", label: "Potentiel ENR", value: "Hydrogène vert", color: "#6B0F0F" },
                { icon: "✅", label: "Prime Territoriale", value: "+15% ", color: "#1A6B3C" },
              ].map((ind) => (
                <div
                  key={ind.label}
                  style={{
                    background: "#FAF6F0",
                    border: "1px solid #EDE2D4",
                    borderRadius: 10,
                    padding: "8px 6px",
                    textAlign: "center",
                  }}
                >
                  <div style={{ fontSize: "1.1rem", marginBottom: 2 }}>{ind.icon}</div>
                  <div
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.68rem",
                      color: "#6B5E4E",
                      lineHeight: 1.15,
                      marginBottom: 3,
                    }}
                  >
                    {ind.label}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-fraunces), Georgia, serif",
                      fontSize: "0.88rem",
                      fontWeight: 700,
                      color: ind.color,
                      lineHeight: 1.1,
                    }}
                  >
                    {ind.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          2. SERVICES RAPIDES (Screen 2 - Figma Style)
      ===================================================== */}
      <section style={{ background: "#FFFFFF", padding: "72px 24px", borderBottom: "1px solid #EDE2D4" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <div
              style={{
                fontFamily: "var(--font-dm-mono), monospace",
                fontSize: "0.75rem",
                letterSpacing: "0.12em",
                color: "#6B0F0F",
                textTransform: "uppercase",
                marginBottom: 8,
                fontWeight: 600,
              }}
            >
              ORIENTATION & OUTILS NUMÉRIQUES
            </div>
            <h2
              style={{
                fontFamily: "var(--font-fraunces), Georgia, serif",
                fontSize: "clamp(1.8rem, 3.2vw, 2.5rem)",
                fontWeight: 700,
                color: "#1C1610",
                margin: "0 0 12px",
              }}
            >
              Accédez rapidement à nos services
            </h2>
            <p
              style={{
                fontFamily: "var(--font-outfit), sans-serif",
                fontSize: "0.95rem",
                color: "#6B5E4E",
                maxWidth: 640,
                margin: "0 auto",
                lineHeight: 1.5,
              }}
            >
              Des outils intelligents conçus pour simplifier et accélérer chacune des démarches de votre projet d&apos;investissement.
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 20,
            }}
          >
            {quickServices.map((service) => (
              <div
                key={service.number}
                onClick={() => handleQuickAction(service.action)}
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #EDE2D4",
                  borderRadius: 14,
                  padding: "22px 20px",
                  cursor: "pointer",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-4px)";
                  e.currentTarget.style.boxShadow = "0 8px 25px rgba(107,15,15,0.08)";
                  e.currentTarget.style.borderColor = "#6B0F0F";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "none";
                  e.currentTarget.style.borderColor = "#EDE2D4";
                }}
              >
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 8,
                    background: "#F4EDE3",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-dm-mono), monospace",
                      fontSize: "0.8rem",
                      fontWeight: 700,
                      color: "#B07A00",
                    }}
                  >
                    {service.number}
                  </span>
                </div>

                <div>
                  <div
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.95rem",
                      fontWeight: 700,
                      color: "#1C1610",
                      marginBottom: 6,
                    }}
                  >
                    {service.title}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.82rem",
                      color: "#6B5E4E",
                      lineHeight: 1.5,
                    }}
                  >
                    {service.description}
                  </div>
                </div>

                <div
                  style={{
                    marginTop: "auto",
                    fontFamily: "var(--font-outfit), sans-serif",
                    fontSize: "0.85rem",
                    fontWeight: 700,
                    color: "#1A6B3C",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  Accéder <span>&rarr;</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =====================================================
          3. PARCOURS INVESTISSEUR (Screen 3 - Figma Style)
      ===================================================== */}
      <section
        id="parcours-investisseur"
        style={{
          background: "#F4EDE3",
          padding: "72px 24px",
          borderBottom: "1px solid #EDE2D4",
        }}
      >
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 40 }}>
            <div
              style={{
                fontFamily: "var(--font-dm-mono), monospace",
                fontSize: "0.75rem",
                letterSpacing: "0.12em",
                color: "#B07A00",
                textTransform: "uppercase",
                marginBottom: 8,
                fontWeight: 600,
              }}
            >
              DE L&apos;IDÉE À LA CROISSANCE
            </div>
            <h2
              style={{
                fontFamily: "var(--font-fraunces), Georgia, serif",
                fontSize: "clamp(1.8rem, 3.2vw, 2.5rem)",
                fontWeight: 700,
                color: "#1C1610",
                margin: "0 0 12px",
              }}
            >
              Parcours de l&apos;Investisseur
            </h2>
            <p
              style={{
                fontFamily: "var(--font-outfit), sans-serif",
                fontSize: "0.95rem",
                color: "#6B5E4E",
                maxWidth: 640,
                margin: "0 auto",
                lineHeight: 1.5,
              }}
            >
              Un accompagnement structuré en 5 étapes clés pour concrétiser votre investissement à chaque phase.
            </p>
          </div>

          {/* Onglets 1 à 5 style Figma */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(5, 1fr)",
              gap: 12,
              marginBottom: 24,
            }}
          >
            {parcoursSteps.map((step) => {
              const isSelected = activeStep === Number(step.number);
              return (
                <div
                  key={step.number}
                  onClick={() => setActiveStep(Number(step.number))}
                  style={{
                    background: isSelected ? "#FFFFFF" : "rgba(255,255,255,0.45)",
                    border: isSelected ? "2px solid #6B0F0F" : "1px solid #EDE2D4",
                    borderRadius: 14,
                    padding: "16px 12px",
                    cursor: "pointer",
                    textAlign: "center",
                    transition: "all 0.2s ease",
                    boxShadow: isSelected ? "0 4px 14px rgba(107,15,15,0.08)" : "none",
                  }}
                >
                  <div
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: "50%",
                      background: isSelected ? step.tone : "#E8DDD0",
                      color: isSelected ? "#FFFFFF" : "#6B5E4E",
                      fontFamily: "var(--font-fraunces), Georgia, serif",
                      fontSize: "1rem",
                      fontWeight: 700,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      margin: "0 auto 8px",
                      transition: "background 0.2s ease",
                    }}
                  >
                    {step.number}
                  </div>
                  <div
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.82rem",
                      fontWeight: isSelected ? 700 : 500,
                      color: isSelected ? "#1C1610" : "#6B5E4E",
                    }}
                  >
                    {step.shortLabel}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Carte de détail de l'étape active */}
          <div
            style={{
              background: "#FFFFFF",
              border: "1px solid #EDE2D4",
              borderRadius: 16,
              padding: "32px 28px",
              boxShadow: "0 8px 30px rgba(0,0,0,0.04)",
              display: "grid",
              gridTemplateColumns: "1.2fr 1fr auto",
              gap: 28,
              alignItems: "center",
            }}
          >
            {/* Colonne 1: Étape et Description */}
            <div>
              <div
                style={{
                  fontFamily: "var(--font-dm-mono), monospace",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  letterSpacing: "0.1em",
                  color: "#1A6B3C",
                  textTransform: "uppercase",
                  marginBottom: 8,
                }}
              >
                {currentStepData.stepBadge}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: 8,
                    background: currentStepData.tone,
                    color: "#FFFFFF",
                    fontFamily: "var(--font-fraunces), Georgia, serif",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  {currentStepData.number}
                </div>
                <h3
                  style={{
                    fontFamily: "var(--font-fraunces), Georgia, serif",
                    fontSize: "1.35rem",
                    fontWeight: 700,
                    color: "#1C1610",
                    margin: 0,
                  }}
                >
                  {currentStepData.title}
                </h3>
              </div>
              <p
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "0.92rem",
                  color: "#6B5E4E",
                  lineHeight: 1.6,
                  margin: 0,
                }}
              >
                {currentStepData.description}
              </p>
            </div>

            {/* Colonne 2: Services CRI associés */}
            <div
              style={{
                background: "#FAF6F0",
                border: "1px solid #EDE2D4",
                borderRadius: 12,
                padding: "16px 18px",
              }}
            >
              <div
                style={{
                  fontFamily: "var(--font-dm-mono), monospace",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  color: "#1A6B3C",
                  textTransform: "uppercase",
                  marginBottom: 10,
                }}
              >
                SERVICES CRI ASSOCIÉS
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {currentStepData.services.map((svc) => (
                  <div
                    key={svc}
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.84rem",
                      color: "#1C1610",
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                    }}
                  >
                    <span style={{ color: "#1A6B3C", fontWeight: 800 }}>✓</span>
                    <span>{svc}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Colonne 3: Bouton action */}
            <div>
              <button
                type="button"
                onClick={() => {
                  if (activeStep === 1 || activeStep === 2) onOpenDocuments();
                  else if (activeStep === 3) onOpenAssistant();
                  else onOpenPrimes();
                }}
                style={{
                  fontFamily: "var(--font-outfit), sans-serif",
                  fontSize: "0.88rem",
                  fontWeight: 600,
                  color: "#1C1610",
                  background: "#FFFFFF",
                  border: "1.5px solid #EDE2D4",
                  borderRadius: 10,
                  padding: "12px 20px",
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: 8,
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = "#6B0F0F";
                  e.currentTarget.style.color = "#6B0F0F";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "#EDE2D4";
                  e.currentTarget.style.color = "#1C1610";
                }}
              >
                <span>En savoir plus</span>
                <span>&rarr;</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* =====================================================
          4. NOUVELLE SECTION: ATOUTS STRATÉGIQUES & 3 IMAGES ANIMÉES
             (Demande utilisateur: texte + 2 ou 3 images animées)
      ===================================================== */}
      <section
        style={{
          background: "#FFFFFF",
          padding: "72px 24px",
          borderBottom: "1px solid #EDE2D4",
        }}
      >
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <div
              style={{
                fontFamily: "var(--font-dm-mono), monospace",
                fontSize: "0.75rem",
                letterSpacing: "0.12em",
                color: "#6B0F0F",
                textTransform: "uppercase",
                marginBottom: 8,
                fontWeight: 600,
              }}
            >
              POTENTIEL ÉCONOMIQUE & SECTEURS CLÉS
            </div>
            <h2
              style={{
                fontFamily: "var(--font-fraunces), Georgia, serif",
                fontSize: "clamp(1.8rem, 3.2vw, 2.5rem)",
                fontWeight: 700,
                color: "#1C1610",
                margin: "0 0 12px",
              }}
            >
              Pourquoi investir à Guelmim-Oued Noun ?
            </h2>
            <p
              style={{
                fontFamily: "var(--font-outfit), sans-serif",
                fontSize: "0.95rem",
                color: "#6B5E4E",
                maxWidth: 680,
                margin: "0 auto",
                lineHeight: 1.6,
              }}
            >
              Porte d&apos;entrée du Sahara marocain, la région combine une situation géostratégique unique, des ressources naturelles inestimables et des incitations fiscales et financières d&apos;exception.
            </p>
          </div>

          {/* 3 Cartes illustrées avec animations d'images */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
              gap: 28,
            }}
          >
            {strategicSectors.map((sector) => (
              <div
                key={sector.title}
                style={{
                  background: "#FAF6F0",
                  border: "1px solid #EDE2D4",
                  borderRadius: 18,
                  overflow: "hidden",
                  display: "flex",
                  flexDirection: "column",
                  boxShadow: "0 4px 20px rgba(0,0,0,0.03)",
                  transition: "transform 0.3s ease, box-shadow 0.3s ease",
                }}
                className="img-animated"
              >
                {/* Image Card avec Badge et Zoom */}
                <div
                  style={{
                    position: "relative",
                    height: 200,
                    overflow: "hidden",
                    background: "#E8DDD0",
                  }}
                >
                  <Image
                    src={sector.image}
                    alt={sector.title}
                    fill
                    style={{ objectFit: "cover" }}
                    sizes="(max-width: 768px) 100vw, 400px"
                  />
                  <div
                    style={{
                      position: "absolute",
                      inset: 0,
                      background: "linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.55) 100%)",
                    }}
                  />
                  {/* Badge Catégorie */}
                  <div
                    style={{
                      position: "absolute",
                      top: 12,
                      left: 12,
                      background: "rgba(255,255,255,0.92)",
                      backdropFilter: "blur(6px)",
                      borderRadius: 999,
                      padding: "4px 12px",
                      fontFamily: "var(--font-dm-mono), monospace",
                      fontSize: "0.7rem",
                      fontWeight: 700,
                      color: "#6B0F0F",
                    }}
                  >
                    {sector.category}
                  </div>
                  {/* Stat Flottante */}
                  <div
                    style={{
                      position: "absolute",
                      bottom: 12,
                      right: 12,
                      background: "rgba(26,107,60,0.92)",
                      backdropFilter: "blur(6px)",
                      color: "#FFFFFF",
                      borderRadius: 6,
                      padding: "4px 10px",
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.76rem",
                      fontWeight: 700,
                    }}
                  >
                    {sector.statBadge}
                  </div>
                </div>

                {/* Contenu textuel */}
                <div style={{ padding: "24px 22px", display: "flex", flexDirection: "column", flex: 1 }}>
                  <h3
                    style={{
                      fontFamily: "var(--font-fraunces), Georgia, serif",
                      fontSize: "1.2rem",
                      fontWeight: 700,
                      color: "#1C1610",
                      margin: "0 0 10px",
                      lineHeight: 1.3,
                    }}
                  >
                    {sector.title}
                  </h3>

                  <p
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.86rem",
                      color: "#6B5E4E",
                      lineHeight: 1.6,
                      margin: "0 0 16px",
                      flex: 1,
                    }}
                  >
                    {sector.description}
                  </p>

                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap", paddingTop: 12, borderTop: "1px solid #EDE2D4" }}>
                    {sector.highlights.map((h) => (
                      <span
                        key={h}
                        style={{
                          fontFamily: "var(--font-outfit), sans-serif",
                          fontSize: "0.74rem",
                          background: "#FFFFFF",
                          border: "1px solid #EDE2D4",
                          borderRadius: 6,
                          padding: "3px 8px",
                          color: "#1C1610",
                          fontWeight: 500,
                        }}
                      >
                        &bull; {h}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =====================================================
          5. DISPOSITIFS & AIDES À L'INVESTISSEMENT (Section Complète)
      ===================================================== */}
      <section
        id="dispositifs-aides"
        style={{
          background: "#F4EDE3",
          padding: "72px 24px",
          borderBottom: "1px solid #EDE2D4",
        }}
      >
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: 48 }}>
            <div
              style={{
                fontFamily: "var(--font-dm-mono), monospace",
                fontSize: "0.75rem",
                letterSpacing: "0.12em",
                color: "#1A6B3C",
                textTransform: "uppercase",
                marginBottom: 8,
                fontWeight: 600,
              }}
            >
              INCITATIONS & SOUTIEN FINANCIER
            </div>
            <h2
              style={{
                fontFamily: "var(--font-fraunces), Georgia, serif",
                fontSize: "clamp(1.8rem, 3.2vw, 2.5rem)",
                fontWeight: 700,
                color: "#1C1610",
                margin: "0 0 12px",
              }}
            >
              Dispositifs & Aides à l&apos;Investissement
            </h2>
            <p
              style={{
                fontFamily: "var(--font-outfit), sans-serif",
                fontSize: "0.95rem",
                color: "#6B5E4E",
                maxWidth: 680,
                margin: "0 auto",
                lineHeight: 1.6,
              }}
            >
              Découvrez les mécanismes de subventions, primes d&apos;investissement et facilités foncières accordés par l&apos;État et le Conseil Régional.
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: 24,
            }}
          >
            {dispositifsList.map((disp) => (
              <div
                key={disp.title}
                style={{
                  background: "#FFFFFF",
                  border: "1px solid #EDE2D4",
                  borderRadius: 16,
                  padding: "26px 22px",
                  display: "flex",
                  flexDirection: "column",
                  boxShadow: "0 4px 18px rgba(0,0,0,0.03)",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-3px)";
                  e.currentTarget.style.boxShadow = "0 8px 24px rgba(107,15,15,0.08)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "0 4px 18px rgba(0,0,0,0.03)";
                }}
              >
                <div style={{ fontSize: "1.8rem", marginBottom: 12 }}>{disp.icon}</div>
                <h3
                  style={{
                    fontFamily: "var(--font-fraunces), Georgia, serif",
                    fontSize: "1.15rem",
                    fontWeight: 700,
                    color: "#1C1610",
                    margin: "0 0 4px",
                  }}
                >
                  {disp.title}
                </h3>
                <div
                  style={{
                    fontFamily: "var(--font-outfit), sans-serif",
                    fontSize: "0.78rem",
                    fontWeight: 600,
                    color: disp.tone,
                    marginBottom: 12,
                  }}
                >
                  {disp.subtitle}
                </div>
                <p
                  style={{
                    fontFamily: "var(--font-outfit), sans-serif",
                    fontSize: "0.85rem",
                    color: "#6B5E4E",
                    lineHeight: 1.55,
                    margin: "0 0 16px",
                  }}
                >
                  {disp.description}
                </p>

                <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: 6, paddingTop: 14, borderTop: "1px solid #FAF6F0" }}>
                  {disp.items.map((item) => (
                    <div
                      key={item}
                      style={{
                        fontFamily: "var(--font-outfit), sans-serif",
                        fontSize: "0.8rem",
                        color: "#1C1610",
                        display: "flex",
                        alignItems: "flex-start",
                        gap: 6,
                      }}
                    >
                      <span style={{ color: disp.tone, fontWeight: 800 }}>&bull;</span>
                      <span>{item}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =====================================================
          6. VALEURS DU CENTRE RÉGIONAL D'INVESTISSEMENT
      ===================================================== */}
      <section style={{ background: "#FFFFFF", padding: "64px 24px", borderBottom: "1px solid #EDE2D4" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 20,
            }}
          >
            {values.map((v) => (
              <div
                key={v.title}
                style={{
                  background: "#FAF6F0",
                  border: "1px solid #EDE2D4",
                  borderRadius: 14,
                  padding: "20px 18px",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontFamily: "var(--font-fraunces), Georgia, serif",
                    fontSize: "1.1rem",
                    fontWeight: 700,
                    color: "#6B0F0F",
                    marginBottom: 6,
                  }}
                >
                  {v.title}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-outfit), sans-serif",
                    fontSize: "0.84rem",
                    color: "#6B5E4E",
                    lineHeight: 1.5,
                  }}
                >
                  {v.description}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* =====================================================
          7. FOOTER INSTITUTIONNEL AVEC LOGO ASSISTANT IA CADRÉ
             & CARTE GPS ANIMÉE (Demande utilisateur)
      ===================================================== */}
      <footer id="contact-footer" style={{ background: "#120606", color: "#FFFFFF", padding: "64px 24px 0" }}>
        <div style={{ maxWidth: 1280, margin: "0 auto" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "280px 1fr 1fr 340px",
              gap: 40,
              paddingBottom: 48,
            }}
          >
            {/* Colonne 1: LOGO OFFICIEL CRI */}
            <div style={{ display: "flex", alignItems: "flex-start", paddingTop: 8 }}>
              <Image
                src="/cri-logo.png"
                alt="Centre Régional d'Investissement Guelmim-Oued Noun"
                width={220}
                height={80}
                priority
                style={{
                  width: "100%",
                  maxWidth: 220,
                  height: "auto",
                  objectFit: "contain",
                  display: "block",
                }}
              />
            </div>

            {/* Colonne 2: Coordonnées & Accueil */}
            <div>
              <div
                style={{
                  fontFamily: "var(--font-dm-mono), monospace",
                  fontSize: "0.7rem",
                  letterSpacing: "0.12em",
                  color: "#B07A00",
                  marginBottom: 16,
                  fontWeight: 700,
                  textTransform: "uppercase",
                }}
              >
                COORDONNÉES & ACCUEIL
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {[
                  { icon: "📍", text: "Avenue Mohammed V, Guelmim 83000,\nRégion Guelmim-Oued Noun, Maroc" },
                  { icon: "📞", text: "+212 5 28 87 22 22 / Standard d'accueil" },
                  { icon: "✉️", text: "contact@guelmiminvest.ma" },
                  { icon: "🕒", text: "Horaires d'ouverture :\nLundi – Vendredi : 08h30 – 16h30" },
                ].map(({ icon, text }) => (
                  <div key={icon} style={{ display: "flex", gap: 10 }}>
                    <span style={{ flexShrink: 0, marginTop: 2 }}>{icon}</span>
                    <span
                      style={{
                        fontFamily: "var(--font-outfit), sans-serif",
                        fontSize: "0.8rem",
                        color: "rgba(255,255,255,0.72)",
                        lineHeight: 1.5,
                        whiteSpace: "pre-line",
                      }}
                    >
                      {text}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Colonne 3: Navigation rapide */}
            <div>
              <div
                style={{
                  fontFamily: "var(--font-dm-mono), monospace",
                  fontSize: "0.7rem",
                  letterSpacing: "0.12em",
                  color: "#B07A00",
                  marginBottom: 16,
                  fontWeight: 700,
                  textTransform: "uppercase",
                }}
              >
                NAVIGATION RAPIDE
              </div>

              {[
                { label: "Accueil", action: () => window.scrollTo({ top: 0, behavior: "smooth" }) },
                { label: "Parcours investisseur", action: () => handleQuickAction("parcours") },
                { label: "Dispositifs & Aides", action: () => handleQuickAction("dispositifs") },
                { label: "Simulateur de primes", action: onOpenPrimes },
                { label: "Analyse documentaire", action: onOpenDocuments },
                { label: "Assistant IA régional", action: onOpenAssistant },
              ].map(({ label, action }) => (
                <div key={label} style={{ marginBottom: 10 }}>
                  <button
                    type="button"
                    onClick={action}
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.82rem",
                      color: "rgba(255,255,255,0.7)",
                      background: "none",
                      border: "none",
                      cursor: "pointer",
                      padding: 0,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                      transition: "color 0.15s ease",
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.color = "#FFFFFF";
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.color = "rgba(255,255,255,0.7)";
                    }}
                  >
                    <span style={{ color: "#B07A00" }}>›</span>
                    <span>{label}</span>
                  </button>
                </div>
              ))}
            </div>

            {/* Colonne 4: CARTE GPS ANIMÉE AVEC RADAR BEACON */}
            <div>
              <div
                style={{
                  fontFamily: "var(--font-dm-mono), monospace",
                  fontSize: "0.7rem",
                  letterSpacing: "0.12em",
                  color: "#B07A00",
                  marginBottom: 16,
                  fontWeight: 700,
                  textTransform: "uppercase",
                }}
              >
                EMPLACEMENT GPS DU CRI
              </div>

              <div
                style={{
                  background: "#1F1010",
                  borderRadius: 14,
                  overflow: "hidden",
                  border: "1px solid rgba(255,255,255,0.12)",
                }}
              >
                <div
                  style={{
                    padding: "10px 14px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    borderBottom: "1px solid rgba(255,255,255,0.08)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ color: "#EF4444" }}>📍</span>
                    <span
                      style={{
                        fontFamily: "var(--font-outfit), sans-serif",
                        fontSize: "0.82rem",
                        fontWeight: 700,
                        color: "#FFFFFF",
                      }}
                    >
                      CRI Guelmim-Oued Noun
                    </span>
                  </div>
                  <span
                    style={{
                      fontFamily: "var(--font-dm-mono), monospace",
                      fontSize: "0.6rem",
                      background: "#6B0F0F",
                      color: "#FFFFFF",
                      padding: "2px 8px",
                      borderRadius: 4,
                      fontWeight: 700,
                    }}
                  >
                    Siège Régional
                  </span>
                </div>

                <div style={{ height: 130, position: "relative", background: "#2A1A1A" }}>
                  <iframe
                    src="https://maps.google.com/maps?q=Centre+R%C3%A9gional+d'Investissement+Guelmim+Oued+Noun&t=&z=16&ie=UTF8&iwloc=&output=embed"
                    title="Emplacement GPS du Centre Régional d'Investissement Guelmim-Oued Noun"
                    loading="lazy"
                    allowFullScreen
                    style={{
                      width: "100%",
                      height: "100%",
                      border: "none",
                      opacity: 0.88,
                    }}
                  />
                  {/* Radar Pulse Beacon */}
                  <div
                    style={{
                      position: "absolute",
                      top: "50%",
                      left: "50%",
                      transform: "translate(-50%, -50%)",
                      pointerEvents: "none",
                    }}
                  >
                    <div
                      style={{
                        width: 14,
                        height: 14,
                        borderRadius: "50%",
                        background: "#EF4444",
                        border: "2px solid #FFFFFF",
                        animation: "radarPulse 2s ease-in-out infinite",
                      }}
                    />
                  </div>
                </div>

                <div
                  style={{
                    padding: "10px 14px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <span
                    style={{
                      fontFamily: "var(--font-dm-mono), monospace",
                      fontSize: "0.68rem",
                      color: "rgba(255,255,255,0.6)",
                    }}
                  >
                    GPS: 28.9866° N, 10.0574° W
                  </span>
                  <a
                    href="https://maps.google.com/?q=Centre+Regional+d'Investissement+Guelmim"
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      fontFamily: "var(--font-outfit), sans-serif",
                      fontSize: "0.74rem",
                      fontWeight: 700,
                      color: "#FFFFFF",
                      background: "linear-gradient(135deg, #1A6B3C, #0F4A28)",
                      border: "none",
                      borderRadius: 6,
                      padding: "5px 12px",
                      textDecoration: "none",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    <span>🗺️</span>
                    <span>Itinéraire ↗</span>
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* Barre Copyright */}
          <div
            style={{
              borderTop: "1px solid rgba(255,255,255,0.08)",
              padding: "16px 0",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: 12,
            }}
          >
            <span style={{ fontFamily: "var(--font-outfit), sans-serif", fontSize: "0.75rem", color: "rgba(255,255,255,0.45)" }}>
              &copy; 2026 Centre Régional d&apos;Investissement Guelmim-Oued Noun. Tous droits réservés.
            </span>
            <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
              <span style={{ fontFamily: "var(--font-outfit), sans-serif", fontSize: "0.75rem", color: "rgba(255,255,255,0.45)" }}>
                Portail Officiel d&apos;Investissement Régional
              </span>
              <span style={{ color: "rgba(255,255,255,0.2)" }}>&bull;</span>
              <span style={{ fontFamily: "var(--font-outfit), sans-serif", fontSize: "0.75rem", color: "rgba(255,255,255,0.45)" }}>
                Royaume du Maroc
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
