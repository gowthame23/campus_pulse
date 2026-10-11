import axios from "../api/axios";

export const supervisorService = {
  getDashboard: () => axios.get("/supervisor/dashboard"),
};
