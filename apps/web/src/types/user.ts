export interface UserProfile {
  id: number;
  name: string;
  account_id: string;
  age: number;
  sex: "M" | "F";
}

export interface UserProfileCreate {
  name: string;
  account_id: string;
  password: string;
  age: number;
  sex: "M" | "F";
}
