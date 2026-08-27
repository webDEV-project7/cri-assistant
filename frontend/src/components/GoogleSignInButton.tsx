"use client";

import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  getGoogleAuthConfig,
  loginWithGoogleCredential,
  type AuthUser,
} from "@/lib/api";


type GoogleCredentialResponse = {
  credential?: string;
};


type GoogleIdApi = {
  initialize: (options: {
    client_id: string;
    callback: (
      response: GoogleCredentialResponse
    ) => void;
    ux_mode?: "popup" | "redirect";
    auto_select?: boolean;
    cancel_on_tap_outside?: boolean;
  }) => void;

  renderButton: (
    element: HTMLElement,
    options: {
      type?: string;
      theme?: string;
      size?: string;
      text?: string;
      shape?: string;
      logo_alignment?: string;
      width?: number;
    },
  ) => void;

  cancel: () => void;
};


declare global {
  interface Window {
    google?: {
      accounts: {
        id: GoogleIdApi;
      };
    };
  }
}


const GOOGLE_SCRIPT_ID =
  "google-identity-services";

const GOOGLE_SCRIPT_URL =
  "https://accounts.google.com/gsi/client";


function loadGoogleIdentityServices():
Promise<void> {
  return new Promise(
    (resolve, reject) => {
      if (
        window.google?.accounts?.id
      ) {
        resolve();
        return;
      }

      const existing =
        document.getElementById(
          GOOGLE_SCRIPT_ID
        ) as HTMLScriptElement | null;

      if (existing) {
        const timer =
          window.setInterval(
            () => {
              if (
                window.google
                  ?.accounts
                  ?.id
              ) {
                window.clearInterval(
                  timer
                );

                resolve();
              }
            },
            100,
          );

        window.setTimeout(
          () => {
            window.clearInterval(
              timer
            );

            if (
              !window.google
                ?.accounts
                ?.id
            ) {
              reject(
                new Error(
                  "Google Identity Services est indisponible."
                )
              );
            }
          },
          10000,
        );

        return;
      }

      const script =
        document.createElement(
          "script"
        );

      script.id =
        GOOGLE_SCRIPT_ID;

      script.src =
        GOOGLE_SCRIPT_URL;

      script.async = true;
      script.defer = true;

      script.onload =
        () => resolve();

      script.onerror =
        () =>
          reject(
            new Error(
              "Impossible de charger Google Identity Services."
            )
          );

      document.head.appendChild(
        script
      );
    },
  );
}


type Props = {
  onSuccess: (
    user: AuthUser
  ) => void;

  onError?: (
    message: string
  ) => void;
};


export default function GoogleSignInButton({
  onSuccess,
  onError,
}: Props) {
  const containerRef =
    useRef<HTMLDivElement | null>(
      null
    );

  const successRef =
    useRef(onSuccess);

  const errorRef =
    useRef(onError);

  const [status, setStatus] =
    useState<
      "loading"
      | "ready"
      | "connecting"
      | "error"
    >("loading");


  useEffect(() => {
    successRef.current =
      onSuccess;
  }, [onSuccess]);


  useEffect(() => {
    errorRef.current =
      onError;
  }, [onError]);


  useEffect(() => {
    let cancelled = false;

    const fail = (
      caughtError: unknown
    ) => {
      if (cancelled) {
        return;
      }

      const message =
        caughtError
          instanceof Error
          ? caughtError.message
          : "Connexion Google impossible.";

      setStatus("error");

      errorRef.current?.(
        message
      );
    };


    const initialize =
      async () => {
        try {
          const config =
            await getGoogleAuthConfig();

          await loadGoogleIdentityServices();

          if (cancelled) {
            return;
          }

          const googleId =
            window.google
              ?.accounts
              ?.id;

          const container =
            containerRef.current;

          if (
            !googleId
            || !container
          ) {
            throw new Error(
              "Google Identity Services est indisponible."
            );
          }

          googleId.initialize({
            client_id:
              config.client_id,

            ux_mode:
              "popup",

            auto_select:
              false,

            cancel_on_tap_outside:
              true,

            callback:
              async (
                response
              ) => {
                const credential =
                  response.credential
                    ?.trim();

                if (!credential) {
                  fail(
                    new Error(
                      "Google n'a pas retourne de credential."
                    )
                  );

                  return;
                }

                try {
                  setStatus(
                    "connecting"
                  );

                  const user =
                    await loginWithGoogleCredential(
                      credential
                    );

                  if (
                    !cancelled
                  ) {
                    successRef.current(
                      user
                    );
                  }

                } catch (
                  caughtError
                ) {
                  fail(
                    caughtError
                  );
                }
              },
          });

          container.innerHTML =
            "";

          googleId.renderButton(
            container,
            {
              type:
                "standard",

              theme:
                "outline",

              size:
                "large",

              text:
                "continue_with",

              shape:
                "pill",

              logo_alignment:
                "left",

              width:
                340,
            },
          );

          setStatus("ready");

        } catch (
          caughtError
        ) {
          fail(
            caughtError
          );
        }
      };


    void initialize();


    return () => {
      cancelled = true;

      try {
        window.google
          ?.accounts
          ?.id
          .cancel();
      } catch {
      }
    };
  }, []);


  return (
    <div
      style={{
        width: "100%",
      }}
    >
      <div
        ref={containerRef}
        style={{
          width: "100%",
          minHeight: "44px",
          display: "flex",
          justifyContent:
            "center",
          alignItems:
            "center",
        }}
      />

      {status === "loading" && (
        <div
          style={{
            marginTop: "6px",
            fontSize: "12px",
            textAlign: "center",
            color: "#64748B",
          }}
        >
          Chargement Google...
        </div>
      )}

      {status ===
        "connecting" && (
        <div
          style={{
            marginTop: "6px",
            fontSize: "12px",
            textAlign: "center",
            color: "#64748B",
          }}
        >
          Connexion Google en cours...
        </div>
      )}

      {status === "error" && (
        <div
          style={{
            marginTop: "6px",
            fontSize: "12px",
            textAlign: "center",
            color: "#B91C1C",
          }}
        >
          Google est temporairement indisponible.
        </div>
      )}
    </div>
  );
}
