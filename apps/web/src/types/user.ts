export interface UserProfile {
  id: number;
  name: string;
  account_id: string;
  age: number;
  sex: "M" | "F";
  onboarding_complete: boolean;
}

export interface UserProfileCreate {
  name: string;
  account_id: string;
  password: string;
  age: number;
  sex: "M" | "F";
}

export interface LoginRequest {
  account_id: string;
  password: string;
}

export interface LoginResponse {
  user_id: number;
  name: string;
  onboarding_complete: boolean;
}
