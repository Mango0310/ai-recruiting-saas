import axios from "axios";

const api = axios.create({
  // /api prefix gets rewritten by Next.js to localhost:8000
  baseURL: "/api",
  timeout: 120000,
});

// Auto-attach JWT token + ngrok bypass header
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("ai_recruit_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  config.headers["ngrok-skip-browser-warning"] = "1";
  return config;
});

// Dashboard
export async function getDashboardStats() {
  const { data } = await api.get("/dashboard/stats");
  return data;
}

export async function getFunnelData() {
  const { data } = await api.get("/dashboard/funnel");
  return data;
}

// Jobs
export async function getJobs() {
  const { data } = await api.get("/jobs");
  return data;
}

export async function getJob(id: number) {
  const { data } = await api.get(`/jobs/${id}`);
  return data;
}

export async function createJob(title: string, jd_text: string) {
  const { data } = await api.post("/jobs", { title, jd_text });
  return data;
}

export async function updateJob(id: number, updates: Record<string, unknown>) {
  const { data } = await api.put(`/jobs/${id}`, updates);
  return data;
}

export async function deleteJob(id: number) {
  const { data } = await api.delete(`/jobs/${id}`);
  return data;
}

export async function reanalyzeJob(id: number) {
  const { data } = await api.post(`/jobs/${id}/reanalyze`);
  return data;
}

// Upload
export async function uploadResumes(jobId: number, files: File[]) {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const { data } = await api.post(`/jobs/${jobId}/resumes`, form);
  return data;
}

// Candidates
export async function getCandidates(jobId: number) {
  const { data } = await api.get(`/jobs/${jobId}/candidates`);
  return data;
}

export async function getCandidate(id: number) {
  const { data } = await api.get(`/candidates/${id}`);
  return data;
}

export async function updateDecision(applicationId: number, hr_decision: string, hr_notes?: string) {
  const { data } = await api.put(`/applications/${applicationId}/decision`, { hr_decision, hr_notes });
  return data;
}

// Pipeline
export async function updateApplicationStatus(applicationId: number, status: string) {
  const { data } = await api.put(`/applications/${applicationId}/status`, { status });
  return data;
}

// Employees
export async function onboardEmployee(data: {
  application_id: number;
  department?: string;
  position?: string;
  reports_to?: string;
  salary?: string;
  hire_date?: string;
  probation_months?: number;
  notes?: string;
}) {
  const { data: resp } = await api.post("/employees", data);
  return resp;
}

export async function getEmployees(status?: string, alert?: string) {
  const params: Record<string, string> = {};
  if (status) params.status = status;
  if (alert) params.alert = alert;
  const { data } = await api.get("/employees", { params });
  return data;
}

export async function getEmployeeStats() {
  const { data } = await api.get("/employees/stats");
  return data;
}

export async function getEmployee(id: number) {
  const { data } = await api.get(`/employees/${id}`);
  return data;
}

export async function createEmployee(data: {
  name: string; position: string; department?: string; salary?: string;
  hire_date?: string; probation_months?: number;
  phone?: string; email?: string; id_number?: string;
  social_insurance?: string; social_insurance_account?: string;
  housing_fund?: string; housing_fund_account?: string;
  bank_name?: string; bank_account?: string;
  education_degree?: string; education_school?: string;
  education_major?: string; education_graduation_year?: number;
  emergency_contact_name?: string; emergency_contact_phone?: string;
  emergency_contact_relation?: string;
  contract_type?: string;
}) {
  const { data: resp } = await api.post("/employees/manual", data);
  return resp;
}

export async function updateEmployee(id: number, data: Record<string, unknown>) {
  const { data: resp } = await api.put(`/employees/${id}`, data);
  return resp;
}

// Probation
export async function getProbationStatus(employeeId: number) {
  const { data } = await api.get(`/employees/${employeeId}/probation`);
  return data;
}

export async function generateProbationEvaluation(employeeId: number, managerNotes?: string) {
  const params = managerNotes ? `?manager_notes=${encodeURIComponent(managerNotes)}` : "";
  const { data } = await api.post(`/employees/${employeeId}/probation/evaluate${params}`);
  return data;
}

export async function addManagerEvaluation(employeeId: number, notes: string, scores?: Record<string, number>) {
  const { data } = await api.post(`/employees/${employeeId}/probation/evaluate/manual`, { notes, scores });
  return data;
}

// Feedback Loop
export async function getFeedbackLoop(employeeId: number) {
  const { data } = await api.get(`/employees/${employeeId}/feedback-loop`);
  return data;
}

// Onboard Token
export async function regenerateOnboardToken(employeeId: number) {
  const { data } = await api.post(`/employees/${employeeId}/regenerate-onboard-token`);
  return data;
}

// Employee Profile
export async function getEmployeeProfileReport(employeeId: number) {
  const { data } = await api.get(`/employees/${employeeId}/profile-report`);
  return data;
}

// Company Knowledge Base
export async function getCompany() {
  const { data } = await api.get("/company");
  return data;
}
export async function updateCompany(body: { name?: string; industry?: string; size?: string; knowledge_text?: string }) {
  const { data } = await api.put("/company", body);
  return data;
}
export async function uploadKnowledge(file: File) {
  const fd = new FormData(); fd.append("file", file);
  const { data } = await api.post("/company/knowledge/upload", fd);
  return data;
}
export async function deleteKnowledge(docId: string) {
  const { data } = await api.delete(`/company/knowledge/${docId}`);
  return data;
}

// Resume
export async function getResumeContent(applicationId: number) {
  const { data } = await api.get(`/applications/${applicationId}/resume`);
  return data;
}

// Interview Feedback
export async function saveFeedback(applicationId: number, feedback: {
  interviewer?: string;
  ai_predictions_match?: string;
  actual_rating?: number;
  key_observations?: string;
  notes?: string;
}) {
  const { data } = await api.put(`/applications/${applicationId}/feedback`, feedback);
  return data;
}

// Match Report
export async function getMatchReport(applicationId: number) {
  const { data } = await api.get(`/applications/${applicationId}/report`);
  return data;
}

export async function reanalyzeApplication(applicationId: number) {
  const { data } = await api.post(`/applications/${applicationId}/reanalyze`);
  return data;
}

export async function generateInterviewQuestions(applicationId: number) {
  const { data } = await api.post(`/applications/${applicationId}/interview-questions`);
  return data;
}

// Talent Pool
export async function searchTalentPool(q?: string, skill?: string, status?: string, type?: string) {
  const params: Record<string, string> = {};
  if (q) params.q = q;
  if (skill) params.skill = skill;
  if (status) params.status = status;
  if (type) params.type = type;
  const { data } = await api.get("/talent-pool", { params });
  return data;
}

export async function semanticSearch(query: string, threshold?: number) {
  const { data } = await api.post("/talent-pool/search", { query, threshold });
  return data;
}

export async function getSimilarCandidates(candidateId: number, topK?: number) {
  const params: Record<string, string> = {};
  if (topK) params.top_k = String(topK);
  const { data } = await api.get(`/talent-pool/similar/${candidateId}`, { params });
  return data;
}

export async function getTalentDetail(id: number) {
  const { data } = await api.get(`/talent-pool/${id}`);
  return data;
}

// Comparison & Briefing
export async function getCompareCandidates(jobId: number) {
  const { data } = await api.get(`/jobs/${jobId}/compare`);
  return data;
}

export async function getBriefing(jobId: number) {
  const { data } = await api.get(`/jobs/${jobId}/briefing`);
  return data;
}
