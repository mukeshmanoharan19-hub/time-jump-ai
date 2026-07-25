import { Configuration, LogLevel, PublicClientApplication } from "@azure/msal-browser";

const clientId = process.env.NEXT_PUBLIC_AZURE_AD_CLIENT_ID ?? "";
const tenantId = process.env.NEXT_PUBLIC_AZURE_AD_TENANT_ID ?? "common";

export const msalConfig: Configuration = {
  auth: {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: typeof window !== "undefined" ? window.location.origin : "http://localhost:3000",
    postLogoutRedirectUri: typeof window !== "undefined" ? window.location.origin : "http://localhost:3000",
  },
  cache: {
    cacheLocation: "localStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      logLevel: LogLevel.Warning,
    },
  },
};

// Minimal delegated scopes for Teams meeting recordings the signed-in user can already open.
export const loginRequest = {
  scopes: [
    "User.Read", // identity (/me) for session broker
    "OnlineMeetings.Read", // Teams online meetings
    "Files.Read", // recording media the user already has access to (OneDrive/SharePoint link)
  ],
};

export const isMsalConfigured = Boolean(clientId);

let pca: PublicClientApplication | null = null;

export function getMsalInstance(): PublicClientApplication {
  if (!pca) {
    pca = new PublicClientApplication(msalConfig);
  }
  return pca;
}
