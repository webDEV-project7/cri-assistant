"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import {
  loginUser,
  registerUser,
  type AuthUser,
} from "@/lib/api";
import GoogleSignInButton from "@/components/GoogleSignInButton";


export type UserProfile = AuthUser;

type GoogleAuthModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (user: UserProfile) => void;
  targetFeatureName: string;
};

type AuthMode =
  | "login"
  | "register";


export default function GoogleAuthModal({
  isOpen,
  onClose,
  onSuccess,
  targetFeatureName,
}: GoogleAuthModalProps) {
  const [mode, setMode] =
    useState<AuthMode>("login");

  const [name, setName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [error, setError] =
    useState("");


  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const resetTimer = window.setTimeout(() => {
      setError("");
      setPassword("");
    }, 0);

    return () => {
      window.clearTimeout(resetTimer);
    };
  }, [isOpen]);


  if (!isOpen) {
    return null;
  }


  function changeMode(
    nextMode: AuthMode,
  ) {
    setMode(nextMode);
    setError("");
    setPassword("");
  }


  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    const cleanName = name.trim();
    const cleanEmail = email.trim();

    setError("");

    if (
      mode === "register"
      && cleanName.length < 2
    ) {
      setError(
        "Veuillez saisir votre nom complet."
      );
      return;
    }

    if (
      !cleanEmail
      || !cleanEmail.includes("@")
    ) {
      setError(
        "Veuillez saisir une adresse e-mail valide."
      );
      return;
    }

    if (password.length < 8) {
      setError(
        "Le mot de passe doit contenir au moins 8 caractères."
      );
      return;
    }

    setIsSubmitting(true);

    try {
      const user =
        mode === "register"
          ? await registerUser({
              name: cleanName,
              email: cleanEmail,
              password,
            })
          : await loginUser({
              email: cleanEmail,
              password,
            });

      setPassword("");

      onSuccess(user);

    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Impossible de vous authentifier."
      );

    } finally {
      setIsSubmitting(false);
    }
  }


  const inputStyle = {
    width: "100%",
    padding: "12px 14px",
    borderRadius: "10px",
    border: "1.5px solid #DED5CA",
    fontSize: "14px",
    outline: "none",
    boxSizing: "border-box" as const,
    background: "#FFFFFF",
    color: "#1A1A1A",
  };


  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background:
          "rgba(15,23,42,0.65)",
        backdropFilter: "blur(4px)",
        zIndex: 10000,
        display: "grid",
        placeItems: "center",
        padding: "16px",
      }}
    >
      <div
        onClick={(event) =>
          event.stopPropagation()
        }
        style={{
          width: "100%",
          maxWidth: "430px",
          background: "#FFFFFF",
          borderRadius: "22px",
          padding: "30px",
          boxShadow:
            "0 20px 50px rgba(0,0,0,0.25)",
          fontFamily:
            "var(--font-inter), sans-serif",
        }}
      >
        <div
          style={{
            width: "54px",
            height: "54px",
            borderRadius: "15px",
            background: "#FEF2F2",
            border: "1px solid #FEE2E2",
            display: "grid",
            placeItems: "center",
            margin: "0 auto 16px",
            color: "#8B0000",
            fontSize: "25px",
            fontWeight: 900,
          }}
        >
          🔐
        </div>

        <h3
          style={{
            fontFamily:
              "var(--font-montserrat), sans-serif",
            fontSize: "21px",
            fontWeight: 800,
            color: "#1A1A1A",
            margin: "0 0 7px",
            textAlign: "center",
          }}
        >
          {mode === "login"
            ? "Connexion à votre espace"
            : "Créer votre compte"}
        </h3>

        <p
          style={{
            fontSize: "13.5px",
            color: "#666",
            lineHeight: 1.55,
            textAlign: "center",
            margin: "0 0 22px",
          }}
        >
          {mode === "login"
            ? (
              <>
                Pour accéder à{" "}
                <strong>
                  {targetFeatureName}
                </strong>
                , connectez-vous à votre
                espace investisseur.
              </>
            )
            : (
              <>
                Créez votre espace
                investisseur pour accéder
                aux services personnalisés
                du CRI.
              </>
            )}
        </p>

        <form onSubmit={handleSubmit}>
          {mode === "register" && (
            <div
              style={{
                marginBottom: "13px",
              }}
            >
              <label
                htmlFor="auth-name"
                style={{
                  display: "block",
                  marginBottom: "6px",
                  fontSize: "12px",
                  fontWeight: 700,
                  color: "#444",
                }}
              >
                Nom complet
              </label>

              <input
                id="auth-name"
                type="text"
                autoComplete="name"
                value={name}
                onChange={(event) =>
                  setName(
                    event.target.value
                  )
                }
                placeholder="Votre nom complet"
                style={inputStyle}
              />
            </div>
          )}

          <div
            style={{
              marginBottom: "13px",
            }}
          >
            <label
              htmlFor="auth-email"
              style={{
                display: "block",
                marginBottom: "6px",
                fontSize: "12px",
                fontWeight: 700,
                color: "#444",
              }}
            >
              Adresse e-mail
            </label>

            <input
              id="auth-email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) =>
                setEmail(
                  event.target.value
                )
              }
              placeholder="nom@exemple.com"
              style={inputStyle}
            />
          </div>

          <div
            style={{
              marginBottom: "15px",
            }}
          >
            <label
              htmlFor="auth-password"
              style={{
                display: "block",
                marginBottom: "6px",
                fontSize: "12px",
                fontWeight: 700,
                color: "#444",
              }}
            >
              Mot de passe
            </label>

            <input
              id="auth-password"
              type="password"
              autoComplete={
                mode === "register"
                  ? "new-password"
                  : "current-password"
              }
              value={password}
              onChange={(event) =>
                setPassword(
                  event.target.value
                )
              }
              placeholder={
                mode === "register"
                  ? "8 caractères minimum"
                  : "Votre mot de passe"
              }
              style={inputStyle}
            />
          </div>

          {error && (
            <div
              role="alert"
              style={{
                color: "#B91C1C",
                background: "#FEF2F2",
                border:
                  "1px solid #FECACA",
                borderRadius: "9px",
                padding: "9px 11px",
                fontSize: "12.5px",
                marginBottom: "13px",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              width: "100%",
              padding: "13px",
              borderRadius: "9999px",
              border: "none",
              background:
                isSubmitting
                  ? "#94A3B8"
                  : "linear-gradient(135deg,#4A0404,#8B0000,#B91C1C)",
              color: "#FFFFFF",
              fontSize: "14.5px",
              fontWeight: 800,
              cursor:
                isSubmitting
                  ? "wait"
                  : "pointer",
            }}
          >
            {isSubmitting
              ? "Veuillez patienter..."
              : mode === "login"
                ? "Se connecter"
                : "Créer mon compte"}
          </button>
        </form>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            margin: "18px 0",
            color: "#9CA3AF",
            fontSize: "11px",
          }}
        >
          <span
            style={{
              flex: 1,
              height: "1px",
              background: "#E5E7EB",
            }}
          />
          ou
          <span
            style={{
              flex: 1,
              height: "1px",
              background: "#E5E7EB",
            }}
          />
        </div>


        <GoogleSignInButton
          onSuccess={onSuccess}
          onError={setError}
        />

        <div
          style={{
            textAlign: "center",
            marginTop: "17px",
            fontSize: "12.5px",
            color: "#666",
          }}
        >
          {mode === "login"
            ? "Pas encore de compte ? "
            : "Vous avez déjà un compte ? "}

          <button
            type="button"
            onClick={() =>
              changeMode(
                mode === "login"
                  ? "register"
                  : "login"
              )
            }
            style={{
              background: "none",
              border: "none",
              padding: 0,
              color: "#8B0000",
              fontWeight: 800,
              cursor: "pointer",
            }}
          >
            {mode === "login"
              ? "Créer un compte"
              : "Se connecter"}
          </button>
        </div>

        <button
          type="button"
          onClick={onClose}
          style={{
            display: "block",
            margin: "15px auto 0",
            background: "none",
            border: "none",
            color: "#777",
            fontSize: "12px",
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          Annuler
        </button>
      </div>
    </div>
  );
}
