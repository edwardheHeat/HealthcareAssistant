export interface UserProfile {
  id: number;
  name: string;
  account_id: string;
  age: number;
  sex: "M" | "F";
<<<<<<< HEAD
  onboarding_complete: boolean;
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
}

export interface UserProfileCreate {
  name: string;
  account_id: string;
  password: string;
  age: number;
  sex: "M" | "F";
}
<<<<<<< HEAD

export interface LoginRequest {
  account_id: string;
  password: string;
}

export interface LoginResponse {
  user_id: number;
  name: string;
  onboarding_complete: boolean;
}
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
