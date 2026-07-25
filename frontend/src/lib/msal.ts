import { AccountInfo, PublicClientApplication } from "@azure/msal-browser";
import { getMsalInstance, isMsalConfigured, loginRequest } from "@/lib/msalConfig";

export { isMsalConfigured, loginRequest };

let initPromise: Promise<PublicClientApplication> | null = null;

export function initMsal(): Promise<PublicClientApplication> {
  if (!isMsalConfigured) {
    return Promise.reject(new Error("MSAL is not configured"));
  }
  if (!initPromise) {
    const instance = getMsalInstance();
    initPromise = instance.initialize().then(() => instance);
  }
  return initPromise;
}

export async function loginAndGetAccessToken(): Promise<{
  accessToken: string;
  expiresOn: Date | null;
  account: AccountInfo;
}> {
  const instance = await initMsal();
  const login = await instance.loginPopup(loginRequest);
  const account = login.account ?? instance.getAllAccounts()[0];
  if (!account) throw new Error("No Microsoft account returned");
  instance.setActiveAccount(account);
  const token = await instance.acquireTokenSilent({
    ...loginRequest,
    account,
  });
  return {
    accessToken: token.accessToken,
    expiresOn: token.expiresOn,
    account,
  };
}

export async function logoutMicrosoft(): Promise<void> {
  if (!isMsalConfigured) return;
  const instance = await initMsal();
  const account = instance.getActiveAccount() ?? instance.getAllAccounts()[0];
  if (account) {
    await instance.logoutPopup({ account });
  }
}
