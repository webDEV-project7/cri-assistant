"use client";

type InvestorServicesViewProps = {
  onOpenPrimes: () => void;
  onOpenDocuments: () => void;
  onOpenContact: () => void;
};

const servicesList = [
  {
    title: "Information et orientation",
    description:
      "Un point d’entrée pour comprendre les principales démarches liées à votre projet d’investissement.",
  },
  {
    title: "Préparation du projet et du dossier",
    description:
      "Un accompagnement pour identifier les informations, documents et procédures susceptibles de concerner votre projet.",
  },
  {
    title: "Primes et incitations financières",
    description:
      "Une orientation vers les dispositifs de soutien de la Charte de l’investissement, selon les critères d’éligibilité applicables.",
  },
  {
    title: "Orientation foncière",
    description:
      "Une aide à l’identification des informations et interlocuteurs utiles concernant le foncier économique.",
  },
  {
    title: "Pré-analyse documentaire",
    description:
      "Une analyse automatique indicative permettant de repérer les pièces potentiellement manquantes ou les éléments à vérifier.",
  },
  {
    title: "Mise en relation et contact",
    description:
      "Une orientation vers les interlocuteurs institutionnels ou partenaires susceptibles d’être concernés par votre projet.",
  },
];

export default function InvestorServicesView({
  onOpenPrimes,
  onOpenDocuments,
  onOpenContact,
}: InvestorServicesViewProps) {
  return (
    <div className="portal-view-container">
      {/* Header Banner */}
      <section className="portal-header-banner">
        <div className="portal-banner-content">
          <nav className="portal-breadcrumb" aria-label="Fil d'Ariane">
            <span className="breadcrumb-current">Accueil / Services aux investisseurs</span>
          </nav>
          <h1>Services aux investisseurs</h1>
          <p>
            Découvrez les principaux services d’information, d’orientation et d’accompagnement proposés aux investisseurs et porteurs de projets.
          </p>
        </div>
      </section>

      {/* Grid of Services */}
      <section className="portal-content-section">
        <div className="services-grid">
          {servicesList.map((service) => (
            <article key={service.title} className="service-card">
              <h3>{service.title}</h3>
              <p>{service.description}</p>
            </article>
          ))}
        </div>

        {/* Action Banner */}
        <div className="services-cta-banner">
          <div className="cta-copy">
            <h2>Prêt à concrétiser votre projet ?</h2>
            <p>
              Utilisez nos outils interactifs pour estimer vos primes d’investissement ou contactez directement un conseiller régional.
            </p>
          </div>
          <div className="cta-actions">
            <button
              type="button"
              className="btn-cta-primary"
              onClick={onOpenPrimes}
            >
              Calculer une prime
            </button>
            <button
              type="button"
              className="btn-cta-secondary"
              onClick={onOpenDocuments}
            >
              Analyser un dossier
            </button>
            <button
              type="button"
              className="btn-cta-outline"
              onClick={onOpenContact}
            >
              Contacter un conseiller
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
