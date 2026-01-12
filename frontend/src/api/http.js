import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8080/api",
//   headers: {
//     Authorization: "Bearer YOUR_TOKEN"
//   }
});

export default api;