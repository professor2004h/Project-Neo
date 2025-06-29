export const USER_NAME_KEY = 'operatorUserName';

export const getStoredUserName = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(USER_NAME_KEY);
};

export const saveUserName = (name: string) => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_NAME_KEY, name);
};
