const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

async function fetcher<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Students API
export const studentsApi = {
  list: () => fetcher<Student[]>("/students"),
  get: (id: number) => fetcher<Student>(`/students/${id}`),
  create: (data: CreateStudentRequest) =>
    fetcher<Student>("/students", { method: "POST", body: JSON.stringify(data) }),
};

// Guardians API
export const guardiansApi = {
  list: () => fetcher<Guardian[]>("/guardians"),
  get: (id: number) => fetcher<Guardian>(`/guardians/${id}`),
  create: (data: CreateGuardianRequest) =>
    fetcher<Guardian>("/guardians", { method: "POST", body: JSON.stringify(data) }),
};

// Invoices API
export const invoicesApi = {
  list: (params?: { student_id?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.student_id) query.append("student_id", params.student_id.toString());
    if (params?.status) query.append("status", params.status);
    return fetcher<Invoice[]>(`/invoices?${query}`);
  },
  get: (id: number) => fetcher<Invoice>(`/invoices/${id}`),
  create: (data: CreateInvoiceRequest) =>
    fetcher<Invoice>("/invoices", { method: "POST", body: JSON.stringify(data) }),
};

// Payments API
export const paymentsApi = {
  list: (params?: { status?: string; phone?: string }) => {
    const query = new URLSearchParams();
    if (params?.status) query.append("status", params.status);
    if (params?.phone) query.append("phone", params.phone);
    return fetcher<PaymentRecord[]>(`/payments?${query}`);
  },
  get: (id: number) => fetcher<PaymentRecord>(`/payments/${id}`),
  initiate: (data: InitiatePaymentRequest) =>
    fetcher<PaymentInitiateResponse>("/payments/initiate", { 
      method: "POST", 
      body: JSON.stringify(data) 
    }),
  getStatus: (transactionId: string) =>
    fetcher<PaymentStatusResponse>(`/payments/status/${transactionId}`),
  simulateCallback: (checkoutId: string, success: boolean = true) =>
    fetcher<SimulateCallbackResponse>(`/payments/simulate-callback/${checkoutId}?success=${success}`, {
      method: "POST"
    }),
};

// Installments API
export const installmentsApi = {
  listPlans: (params?: { student_id?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.student_id) query.append("student_id", params.student_id.toString());
    if (params?.status) query.append("status", params.status);
    return fetcher<InstallmentPlan[]>(`/installments/plans?${query}`);
  },
  getPlan: (id: number) => fetcher<InstallmentPlan>(`/installments/plans/${id}`),
  createPlan: (data: CreateInstallmentPlanRequest) =>
    fetcher<InstallmentPlan>("/installments/plans", { method: "POST", body: JSON.stringify(data) }),
  payInstallment: (installmentId: number, data: PayInstallmentRequest) =>
    fetcher<PaymentInitiateResponse>(`/installments/${installmentId}/pay`, { method: "POST", body: JSON.stringify(data) }),
};

// Loans API
export const loansApi = {
  list: (params?: { guardian_id?: number; status?: string }) => {
    const query = new URLSearchParams();
    if (params?.guardian_id) query.append("guardian_id", params.guardian_id.toString());
    if (params?.status) query.append("status", params.status);
    return fetcher<Loan[]>(`/loans?${query}`);
  },
  get: (id: number) => fetcher<Loan>(`/loans/${id}`),
  apply: (data: LoanApplicationRequest) =>
    fetcher<Loan>("/loans/apply", { method: "POST", body: JSON.stringify(data) }),
  approve: (id: number, data: ApproveLoanRequest) =>
    fetcher<Loan>(`/loans/${id}/approve`, { method: "POST", body: JSON.stringify(data) }),
  disburse: (id: number) =>
    fetcher<Loan>(`/loans/${id}/disburse`, { method: "POST" }),
  getCreditScore: (guardianId: number) =>
    fetcher<CreditScore>(`/loans/credit-score/${guardianId}`),
};

// Settings API
export const settingsApi = {
  getMpesaSettings: () => fetcher<MpesaSettingsResponse>("/settings/mpesa"),
  saveMpesaSettings: (data: SaveMpesaSettingsRequest) =>
    fetcher<MpesaSettingsResponse>("/settings/mpesa", { 
      method: "POST", 
      body: JSON.stringify(data) 
    }),
  testConnection: () => fetcher<TestConnectionResponse>("/settings/mpesa/test", { method: "POST" }),
  clearMpesaSettings: () => fetcher<{ message: string }>("/settings/mpesa", { method: "DELETE" }),
};

// Analytics API
export const analyticsApi = {
  getOverview: () => fetcher<AnalyticsOverview>("/analytics/overview"),
  getCollectionTrends: (params?: { period?: string }) => {
    const query = new URLSearchParams();
    if (params?.period) query.append("period", params.period);
    return fetcher<CollectionTrend[]>(`/analytics/collection-trends?${query}`);
  },
  getAtRiskStudents: () => fetcher<AtRiskStudent[]>("/analytics/at-risk-students"),
  getPredictions: () => fetcher<PaymentPrediction>("/analytics/predictions"),
};

// Types
export interface Guardian {
  id: number;
  first_name: string;
  last_name: string;
  phone: string;
  email?: string;
  id_number?: string;
  created_at: string;
}

export interface Student {
  id: number;
  admission_number: string;
  first_name: string;
  last_name: string;
  guardian_id?: number;
  class_name?: string;
  status: string;
  created_at: string;
  guardian?: Guardian;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  student_id: number;
  total_amount: number;
  paid_amount: number;
  balance: number;
  due_date: string;
  status: string;
  description?: string;
  term?: string;
  year?: number;
  created_at: string;
  student?: Student;
}

export interface PaymentRecord {
  id: number;
  transaction_id: string;
  checkout_request_id?: string;
  merchant_request_id?: string;
  amount: number;
  phone: string;
  account_reference?: string;
  status: string;
  mpesa_receipt_number?: string;
  result_code?: string;
  result_desc?: string;
  created_at: string;
  completed_at?: string;
}

export interface PaymentInitiateResponse {
  success: boolean;
  message: string;
  transaction_id: string;
  checkout_id?: string;
}

export interface PaymentStatusResponse {
  success: boolean;
  message: string;
  status: string;
  transaction_id: string;
  checkout_id: string;
  mpesa_receipt?: string;
  result_code?: string;
  result_desc?: string;
}

export interface SimulateCallbackResponse {
  message: string;
  transaction_id: string;
  status: string;
  mpesa_receipt?: string;
}

export interface InstallmentPlan {
  id: number;
  plan_number: string;
  invoice_id: number;
  student_id: number;
  total_amount: number;
  number_of_installments: number;
  installment_amount: number;
  frequency: string;
  start_date: string;
  paid_amount: number;
  remaining_amount: number;
  paid_installments: number;
  status: string;
  installments?: Installment[];
  student?: Student;
}

export interface Installment {
  id: number;
  plan_id: number;
  installment_number: number;
  amount: number;
  due_date: string;
  paid_amount: number;
  paid_date?: string;
  status: string;
  late_fee_applied: number;
}

export interface Loan {
  id: number;
  loan_number: string;
  guardian_id: number;
  student_id?: number;
  principal_amount: number;
  interest_rate: number;
  total_amount: number;
  tenure_months: number;
  monthly_repayment: number;
  repaid_amount: number;
  outstanding_amount: number;
  status: string;
  credit_score_at_application?: number;
  created_at: string;
  guardian?: Guardian;
  student?: Student;
  repayments?: LoanRepayment[];
}

export interface LoanRepayment {
  id: number;
  loan_id: number;
  repayment_number: number;
  scheduled_amount: number;
  due_date: string;
  paid_amount: number;
  paid_date?: string;
  status: string;
  late_fee: number;
}

export interface CreditScore {
  id: number;
  guardian_id: number;
  credit_score: number;
  risk_level: string;
  max_loan_amount: number;
  recommended_interest_rate: number;
  total_payments: number;
  on_time_payments: number;
  late_payments: number;
  last_calculated: string;
}

export interface AnalyticsOverview {
  total_invoiced: number;
  total_collected: number;
  total_outstanding: number;
  collection_rate: number;
  total_students: number;
  paying_students: number;
  active_installment_plans: number;
  active_loans: number;
  on_time_payment_rate: number;
  overdue_count: number;
}

export interface CollectionTrend {
  period: string;
  invoiced: number;
  collected: number;
  collection_rate: number;
}

export interface AtRiskStudent {
  student_id: number;
  student_name: string;
  admission_number: string;
  outstanding_amount: number;
  days_overdue: number;
  risk_score: number;
  guardian_phone: string;
}

export interface PaymentPrediction {
  expected_collection_next_30_days: number;
  at_risk_amount: number;
  predicted_default_rate: number;
  recommendations: string[];
}

// Settings types
export interface MpesaSettingsResponse {
  consumer_key_set: boolean;
  consumer_secret_set: boolean;
  environment: string;
  callback_url: string;
  shortcode: string;
  is_configured: boolean;
  last_updated?: string;
}

export interface SaveMpesaSettingsRequest {
  consumer_key: string;
  consumer_secret: string;
  environment?: string;
  callback_url?: string;
}

export interface TestConnectionResponse {
  success: boolean;
  message: string;
  access_token_obtained: boolean;
  environment: string;
}

// Request types
export interface CreateGuardianRequest {
  first_name: string;
  last_name: string;
  phone: string;
  email?: string;
  id_number?: string;
}

export interface CreateStudentRequest {
  admission_number: string;
  first_name: string;
  last_name: string;
  guardian_id: number;
  class_name?: string;
}

export interface CreateInvoiceRequest {
  student_id: number;
  total_amount: number;
  due_date: string;
  description?: string;
  term?: string;
  year?: number;
}

export interface InitiatePaymentRequest {
  amount: number;
  phone: string;
  account_reference: string;
  transaction_desc?: string;
  invoice_id?: number;
  student_id?: number;
}

export interface CreateInstallmentPlanRequest {
  invoice_id: number;
  number_of_installments: number;
  frequency?: string;
  start_date?: string;
}

export interface PayInstallmentRequest {
  phone: string;
  amount?: number;
}

export interface LoanApplicationRequest {
  guardian_id: number;
  student_id?: number;
  invoice_id?: number;
  principal_amount: number;
  tenure_months: number;
}

export interface ApproveLoanRequest {
  approved_by: string;
  notes?: string;
}
