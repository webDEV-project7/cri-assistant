"use client";

type ProceduresViewProps = {
  onOpenDocuments: () => void;
  onOpenContact: () => void;
};

const steps = [
  {
    number: "1",
    title: "Idée & information",
    description:
      "Clarifiez votre idée et identifiez les informations nécessaires avant de structurer votre projet.",
    services: [
      "Information territoriale",
      "Orientation initiale",
      "Opportunités régionales",
    ],
    tone: "green",
  },
  {
    number: "2",
    title: "Préparation du projet",
    description:
      "Structurez votre projet, vérifiez les éléments nécessaires et préparez votre dossier.",
    services: [
      "Pré-analyse documentaire",
      "Montage du dossier",
      "Identification des pièces",
    ],
    tone: "gold",
  },
  {
    number: "3",
    title: "Instruction des demandes",
    description:
      "Déposez vos demandes et suivez les étapes administratives nécessaires à votre investissement.",
    services: [
      "Orientation des démarches",
      "Suivi du dossier",
      "Information administrative",
    ],
    tone: "red",
  },
  {
    number: "4",
    title: "Réalisation du projet",
    description:
      "Concrétisez votre investissement en mobilisant les services et partenaires adaptés.",
    services: [
      "Mise en relation",
      "Appui opérationnel",
      "Facilitation",
    ],
    tone: "green",
  },
  {
    number: "5",
    title: "Suivi & croissance",
    description:
      "Poursuivez le développement de votre projet et identifiez de nouvelles opportunités.",
    services: [
      "Suivi personnalisé",
      "Développement",
      "Orientation croissance",
    ],
    tone: "gold",
  },
];

const benefits = [
  "Démarches mieux structurées",
  "Délais mieux maîtrisés",
  "Accompagnement de proximité",
  "Information claire",
];

export default function ProceduresView({
  onOpenDocuments,
  onOpenContact,
}: ProceduresViewProps) {
  return (
    <div className="journey-page">
      <style>{`
        .journey-page {
          min-height: calc(100vh - 72px);
          padding: 42px 25px 50px;
          background:
            radial-gradient(
              circle at 50% 0,
              rgba(216,141,24,.08),
              transparent 34%
            ),
            #faf8f4;
          color: #1f251f;
          font-family: var(--font-inter), Arial, sans-serif;
        }

        .journey-page * {
          box-sizing: border-box;
        }

        .journey-inner {
          width: min(1120px,100%);
          margin: 0 auto;
        }

        .journey-header {
          text-align: center;
          margin-bottom: 33px;
        }

        .journey-kicker {
          margin: 0 0 7px;
          color: #9e1723;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: .12em;
          text-transform: uppercase;
        }

        .journey-header h1 {
          margin: 0;
          color: #201d19;
          font-family: Georgia, "Times New Roman", serif;
          font-size: clamp(32px,3.4vw,47px);
          letter-spacing: -.025em;
        }

        .journey-header p {
          max-width: 610px;
          margin: 10px auto 0;
          color: #71766f;
          font-size: 12px;
          line-height: 1.65;
        }

        .journey-progress {
          display: grid;
          grid-template-columns: repeat(5,minmax(0,1fr));
          margin: 0 auto 31px;
        }

        .journey-progress-item {
          position: relative;
          text-align: center;
        }

        .journey-progress-item::after {
          content: "";
          position: absolute;
          top: 15px;
          left: 58%;
          width: 84%;
          height: 1px;
          background: #dfccb1;
        }

        .journey-progress-item:last-child::after {
          display: none;
        }

        .journey-progress-circle {
          position: relative;
          z-index: 2;
          width: 31px;
          height: 31px;
          margin: 0 auto 7px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          color: #fff;
          font-size: 10px;
          font-weight: 900;
          box-shadow: 0 4px 10px rgba(0,0,0,.09);
        }

        .journey-progress-circle.green {
          background: #08764d;
        }

        .journey-progress-circle.gold {
          background: #d58b14;
        }

        .journey-progress-circle.red {
          background: #a71827;
        }

        .journey-progress-item span:last-child {
          color: #625e58;
          font-size: 8px;
          font-weight: 700;
        }

        .journey-list {
          display: grid;
          gap: 12px;
        }

        .journey-card {
          display: grid;
          grid-template-columns:
            48px
            minmax(0,1fr)
            minmax(210px,270px)
            24px;
          gap: 18px;
          align-items: center;
          padding: 18px 20px;
          border: 1px solid #eadfce;
          border-radius: 14px;
          background: #fff;
          box-shadow: 0 7px 22px rgba(70,47,24,.045);
        }

        .journey-number {
          width: 37px;
          height: 37px;
          display: grid;
          place-items: center;
          border-radius: 50%;
          color: #fff;
          font-size: 12px;
          font-weight: 900;
        }

        .journey-card.green .journey-number {
          background: #08764d;
        }

        .journey-card.gold .journey-number {
          background: #d58b14;
        }

        .journey-card.red .journey-number {
          background: #a71827;
        }

        .journey-main h2 {
          margin: 0 0 5px;
          color: #26221d;
          font-family: Georgia, "Times New Roman", serif;
          font-size: 16px;
        }

        .journey-main p {
          margin: 0;
          color: #72766f;
          font-size: 10px;
          line-height: 1.55;
        }

        .journey-services {
          padding: 10px 12px;
          border-radius: 9px;
          background: #f5f8f5;
        }

        .journey-card.gold .journey-services {
          background: #fff9ed;
        }

        .journey-card.red .journey-services {
          background: #fff5f5;
        }

        .journey-services strong {
          display: block;
          margin-bottom: 5px;
          color: #08764d;
          font-size: 8.5px;
          text-transform: uppercase;
          letter-spacing: .06em;
        }

        .journey-card.gold .journey-services strong {
          color: #b76c06;
        }

        .journey-card.red .journey-services strong {
          color: #9e1723;
        }

        .journey-services span {
          display: block;
          color: #5f6962;
          font-size: 8.5px;
          line-height: 1.55;
        }

        .journey-arrow {
          color: #b29062;
          font-size: 20px;
        }

        .journey-actions {
          margin-top: 20px;
          padding: 18px 20px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 18px;
          border: 1px solid #e8dece;
          border-radius: 14px;
          background: linear-gradient(100deg,#f5f8f5,#fff);
        }

        .journey-actions h3 {
          margin: 0 0 3px;
          font-family: Georgia, "Times New Roman", serif;
          font-size: 15px;
        }

        .journey-actions p {
          margin: 0;
          color: #737971;
          font-size: 9.5px;
        }

        .journey-buttons {
          display: flex;
          gap: 9px;
        }

        .journey-primary,
        .journey-secondary {
          min-height: 40px;
          padding: 0 17px;
          border-radius: 8px;
          font-family: inherit;
          font-size: 10px;
          font-weight: 800;
          cursor: pointer;
        }

        .journey-primary {
          color: #fff;
          border: 1px solid #08764d;
          background: #08764d;
        }

        .journey-secondary {
          color: #9e1723;
          border: 1px solid #b32734;
          background: #fff;
        }

        .journey-benefits {
          margin-top: 18px;
          display: grid;
          grid-template-columns: repeat(4,minmax(0,1fr));
          border: 1px solid #eadfce;
          border-radius: 13px;
          background: #fff;
          overflow: hidden;
        }

        .journey-benefit {
          min-height: 70px;
          padding: 15px;
          display: grid;
          place-items: center;
          text-align: center;
          border-right: 1px solid #eee5d9;
          color: #536359;
          font-size: 9px;
          font-weight: 700;
        }

        .journey-benefit:last-child {
          border-right: 0;
        }

        @media (max-width: 820px) {
          .journey-progress {
            display: none;
          }

          .journey-card {
            grid-template-columns: 42px 1fr;
          }

          .journey-services {
            grid-column: 2;
          }

          .journey-arrow {
            display: none;
          }

          .journey-actions {
            align-items: flex-start;
            flex-direction: column;
          }

          .journey-benefits {
            grid-template-columns: repeat(2,1fr);
          }
        }

        @media (max-width: 520px) {
          .journey-page {
            padding: 28px 14px 38px;
          }

          .journey-card {
            padding: 15px;
          }

          .journey-buttons {
            width: 100%;
            flex-direction: column;
          }

          .journey-primary,
          .journey-secondary {
            width: 100%;
          }

          .journey-benefits {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <div className="journey-inner">
        <header className="journey-header">
          <p className="journey-kicker">
            De l’idée à la croissance
          </p>

          <h1>Parcours investisseur</h1>

          <p>
            Un accompagnement structuré pour concrétiser
            votre projet d’investissement étape par étape.
          </p>
        </header>

        <div
          className="journey-progress"
          aria-label="Étapes du parcours investisseur"
        >
          {steps.map((step) => (
            <div
              className="journey-progress-item"
              key={step.number}
            >
              <span
                className={`journey-progress-circle ${step.tone}`}
              >
                {step.number}
              </span>

              <span>{step.title}</span>
            </div>
          ))}
        </div>

        <section className="journey-list">
          {steps.map((step) => (
            <article
              className={`journey-card ${step.tone}`}
              key={step.number}
            >
              <div className="journey-number">
                {step.number}
              </div>

              <div className="journey-main">
                <h2>{step.title}</h2>
                <p>{step.description}</p>
              </div>

              <div className="journey-services">
                <strong>Nos services</strong>

                {step.services.map((service) => (
                  <span key={service}>
                    {service}
                  </span>
                ))}
              </div>

              <span
                className="journey-arrow"
                aria-hidden="true"
              >
                ›
              </span>
            </article>
          ))}
        </section>

        <section className="journey-actions">
          <div>
            <h3>
              Besoin d’un accompagnement personnalisé ?
            </h3>

            <p>
              Préparez votre dossier ou échangez avec
              les équipes du CRI.
            </p>
          </div>

          <div className="journey-buttons">
            <button
              type="button"
              className="journey-secondary"
              onClick={onOpenDocuments}
            >
              Pré-analyser mes documents
            </button>

            <button
              type="button"
              className="journey-primary"
              onClick={onOpenContact}
            >
              Nous contacter
            </button>
          </div>
        </section>

        <section className="journey-benefits">
          {benefits.map((benefit) => (
            <div
              className="journey-benefit"
              key={benefit}
            >
              ✓ {benefit}
            </div>
          ))}
        </section>
      </div>
    </div>
  );
}