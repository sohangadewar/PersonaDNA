import axios from "axios";

export const api = axios.create({
  baseURL: "https://personadna-1.onrender.com",
});
