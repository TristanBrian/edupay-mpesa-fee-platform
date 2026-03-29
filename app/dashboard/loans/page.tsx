"use client";

import { useState } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Search, TrendingUp, AlertCircle, CheckCircle, Clock, Wallet, ChevronRight } from "lucide-react";
import { formatCurrency, formatDate, getStatusBadgeVariant } from "@/lib/utils";

interface Loan {
  id: number;
  loan_number: string;
  guardian_name: string;
  guardian_phone: string;
  student_name: string;
  principal_amount: number;
  interest_rate: number;
  total_amount: number;
  tenure_months: number;
  monthly_repayment: number;
  repaid_amount: number;
  outstanding_amount: number;
  credit_score: number;
  status: string;
  created_at: string;
  next_due_date: string;
}

interface CreditScoreData {
  guardian_id: number;
  guardian_name: string;
  credit_score: number;
  risk_level: string;
  max_loan_amount: number;
  on_time_payments: number;
  late_payments: number;
  total_payments: number;
}

// Demo data
const demoLoans: Loan[] = [
  { id: 1, loan_number: "LN-2024-001", guardian_name: "James Kamau", guardian_phone: "+254712345678", student_name: "John Kamau", principal_amount: 50000, interest_rate: 12, total_amount: 56000, tenure_months: 6, monthly_repayment: 9334, repaid_amount: 28000, outstanding_amount: 28000, credit_score: 720, status: "active", created_at: "2024-01-15", next_due_date: "2024-04-15" },
  { id: 2, loan_number: "LN-2024-002", guardian_name: "Paul Ochieng", guardian_phone: "+254734567890", student_name: "Peter Ochieng", principal_amount: 40000, interest_rate: 15, total_amount: 46000, tenure_months: 4, monthly_repayment: 11500, repaid_amount: 0, outstanding_amount: 46000, credit_score: 580, status: "pending_approval", created_at: "2024-03-10", next_due_date: "-" },
  { id: 3, loan_number: "LN-2024-003", guardian_name: "Daniel Kiprop", guardian_phone: "+254756789012", student_name: "David Kiprop", principal_amount: 60000, interest_rate: 18, total_amount: 70800, tenure_months: 6, monthly_repayment: 11800, repaid_amount: 11800, outstanding_amount: 59000, credit_score: 450, status: "overdue", created_at: "2024-02-01", next_due_date: "2024-03-01" },
  { id: 4, loan_number: "LN-2024-004", guardian_name: "Jane Wanjiku", guardian_phone: "+254723456789", student_name: "Mary Wanjiku", principal_amount: 30000, interest_rate: 10, total_amount: 33000, tenure_months: 3, monthly_repayment: 11000, repaid_amount: 33000, outstanding_amount: 0, credit_score: 800, status: "paid", created_at: "2023-12-01", next_due_date: "-" },
];

const demoCreditScores: CreditScoreData[] = [
  { guardian_id: 1, guardian_name: "James Kamau", credit_score: 720, risk_level: "low", max_loan_amount: 100000, on_time_payments: 15, late_payments: 2, total_payments: 17 },
  { guardian_id: 2, guardian_name: "Jane Wanjiku", credit_score: 800, risk_level: "low", max_loan_amount: 150000, on_time_payments: 25, late_payments: 0, total_payments: 25 },
  { guardian_id: 3, guardian_name: "Paul Ochieng", credit_score: 580, risk_level: "medium", max_loan_amount: 50000, on_time_payments: 8, late_payments: 5, total_payments: 13 },
  { guardian_id: 4, guardian_name: "Daniel Kiprop", credit_score: 450, risk_level: "high", max_loan_amount: 25000, on_time_payments: 3, late_payments: 8, total_payments: 11 },
];

function getCreditScoreColor(score: number): string {
  if (score >= 700) return "text-success";
  if (score >= 550) return "text-warning";
  return "text-destructive";
}

function getRiskBadgeVariant(risk: string): "success" | "warning" | "destructive" {
  switch (risk) {
    case "low": return "success";
    case "medium": return "warning";
    default: return "destructive";
  }
}

export default function LoansPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isApplyDialogOpen, setIsApplyDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("loans");

  const filteredLoans = demoLoans.filter((loan) => {
    const matchesSearch =
      loan.guardian_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      loan.loan_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      loan.student_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || loan.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const activeLoans = demoLoans.filter(l => l.status === "active").length;
  const pendingApproval = demoLoans.filter(l => l.status === "pending_approval").length;
  const totalDisbursed = demoLoans.filter(l => ["active", "paid", "overdue"].includes(l.status)).reduce((sum, l) => sum + l.principal_amount, 0);
  const totalOutstanding = demoLoans.reduce((sum, l) => sum + l.outstanding_amount, 0);

  return (
    <div className="flex flex-col">
      <Header
        title="Micro-Loans"
        description="Manage fee loans and credit scoring"
      />

      <div className="flex-1 space-y-4 p-6">
        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Loans</CardTitle>
              <Wallet className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeLoans}</div>
              <p className="text-xs text-muted-foreground">Currently running</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Approval</CardTitle>
              <Clock className="h-4 w-4 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-warning">{pendingApproval}</div>
              <p className="text-xs text-muted-foreground">Awaiting review</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Disbursed</CardTitle>
              <TrendingUp className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(totalDisbursed)}</div>
              <p className="text-xs text-muted-foreground">All time</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Outstanding</CardTitle>
              <AlertCircle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">{formatCurrency(totalOutstanding)}</div>
              <p className="text-xs text-muted-foreground">To be collected</p>
            </CardContent>
          </Card>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="loans">Loans</TabsTrigger>
              <TabsTrigger value="credit-scores">Credit Scores</TabsTrigger>
            </TabsList>

            <Dialog open={isApplyDialogOpen} onOpenChange={setIsApplyDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Apply for Loan
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Loan Application</DialogTitle>
                  <DialogDescription>
                    Apply for a micro-loan to cover school fees.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="space-y-2">
                    <Label>Select Guardian</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select guardian" />
                      </SelectTrigger>
                      <SelectContent>
                        {demoCreditScores.map((cs) => (
                          <SelectItem key={cs.guardian_id} value={cs.guardian_id.toString()}>
                            {cs.guardian_name} (Score: {cs.credit_score})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Select Student</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select student" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">John Kamau (ADM-001)</SelectItem>
                        <SelectItem value="2">Peter Ochieng (ADM-003)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Loan Amount (KES)</Label>
                      <Input type="number" placeholder="Enter amount" />
                    </div>
                    <div className="space-y-2">
                      <Label>Tenure (Months)</Label>
                      <Select>
                        <SelectTrigger>
                          <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="3">3 Months</SelectItem>
                          <SelectItem value="6">6 Months</SelectItem>
                          <SelectItem value="9">9 Months</SelectItem>
                          <SelectItem value="12">12 Months</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="rounded-lg border bg-muted/50 p-4">
                    <p className="text-sm font-medium mb-2">Loan Estimate</p>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Principal:</span>
                        <span className="font-medium">KES 50,000</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Interest Rate:</span>
                        <span className="font-medium">12% p.a.</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Total Repayment:</span>
                        <span className="font-medium">KES 56,000</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Monthly Payment:</span>
                        <span className="font-medium">KES 9,334</span>
                      </div>
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsApplyDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button onClick={() => setIsApplyDialogOpen(false)}>
                    Submit Application
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <TabsContent value="loans" className="space-y-4">
            {/* Filters */}
            <div className="flex gap-4">
              <div className="relative flex-1 max-w-sm">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search loans..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending_approval">Pending Approval</SelectItem>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="overdue">Overdue</SelectItem>
                  <SelectItem value="paid">Paid</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Loans List */}
            <div className="grid gap-4">
              {filteredLoans.length === 0 ? (
                <Card>
                  <CardContent className="flex items-center justify-center py-8">
                    <p className="text-muted-foreground">No loans found</p>
                  </CardContent>
                </Card>
              ) : (
                filteredLoans.map((loan) => (
                  <Card key={loan.id} className="hover:bg-accent/50 transition-colors">
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 space-y-3">
                          <div className="flex items-center gap-3">
                            <span className="font-mono text-sm text-muted-foreground">{loan.loan_number}</span>
                            <Badge variant={getStatusBadgeVariant(loan.status)}>
                              {loan.status.replace("_", " ")}
                            </Badge>
                            <span className={`text-sm font-medium ${getCreditScoreColor(loan.credit_score)}`}>
                              Score: {loan.credit_score}
                            </span>
                          </div>
                          
                          <div>
                            <h3 className="font-semibold">{loan.guardian_name}</h3>
                            <p className="text-sm text-muted-foreground">
                              Student: {loan.student_name} | {loan.guardian_phone}
                            </p>
                          </div>

                          <div className="flex items-center gap-6 text-sm">
                            <div>
                              <span className="text-muted-foreground">Principal: </span>
                              <span className="font-medium">{formatCurrency(loan.principal_amount)}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Interest: </span>
                              <span className="font-medium">{loan.interest_rate}% p.a.</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Total: </span>
                              <span className="font-medium">{formatCurrency(loan.total_amount)}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Monthly: </span>
                              <span className="font-medium">{formatCurrency(loan.monthly_repayment)}</span>
                            </div>
                          </div>

                          {loan.status !== "pending_approval" && (
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-muted-foreground">
                                  Repaid: {formatCurrency(loan.repaid_amount)} / {formatCurrency(loan.total_amount)}
                                </span>
                                <span className="font-medium">
                                  {Math.round((loan.repaid_amount / loan.total_amount) * 100)}%
                                </span>
                              </div>
                              <Progress value={(loan.repaid_amount / loan.total_amount) * 100} />
                            </div>
                          )}
                        </div>

                        <div className="ml-6 flex flex-col items-end gap-2">
                          {loan.status === "pending_approval" ? (
                            <div className="flex gap-2">
                              <Button variant="outline" size="sm">Reject</Button>
                              <Button size="sm">Approve</Button>
                            </div>
                          ) : loan.status !== "paid" ? (
                            <div className="text-right">
                              <p className="text-sm text-muted-foreground">Next Payment</p>
                              <p className="font-medium">{formatCurrency(loan.monthly_repayment)}</p>
                              <p className="text-xs text-muted-foreground">Due: {formatDate(loan.next_due_date)}</p>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1 text-success">
                              <CheckCircle className="h-4 w-4" />
                              <span className="text-sm font-medium">Fully Paid</span>
                            </div>
                          )}
                          <Button variant="ghost" size="sm">
                            View Details
                            <ChevronRight className="ml-1 h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          <TabsContent value="credit-scores" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              {demoCreditScores.map((cs) => (
                <Card key={cs.guardian_id}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">{cs.guardian_name}</CardTitle>
                        <CardDescription>Guardian Credit Profile</CardDescription>
                      </div>
                      <Badge variant={getRiskBadgeVariant(cs.risk_level)}>
                        {cs.risk_level} risk
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-center">
                      <div className="relative flex items-center justify-center">
                        <svg className="w-32 h-32 transform -rotate-90">
                          <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            className="text-muted"
                          />
                          <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            strokeDasharray={`${(cs.credit_score / 1000) * 352} 352`}
                            className={getCreditScoreColor(cs.credit_score)}
                          />
                        </svg>
                        <div className="absolute text-center">
                          <span className={`text-3xl font-bold ${getCreditScoreColor(cs.credit_score)}`}>
                            {cs.credit_score}
                          </span>
                          <p className="text-xs text-muted-foreground">/ 1000</p>
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="rounded-lg border p-3">
                        <p className="text-muted-foreground">Max Loan Amount</p>
                        <p className="text-lg font-semibold">{formatCurrency(cs.max_loan_amount)}</p>
                      </div>
                      <div className="rounded-lg border p-3">
                        <p className="text-muted-foreground">Payment History</p>
                        <p className="text-lg font-semibold">
                          <span className="text-success">{cs.on_time_payments}</span>
                          {" / "}
                          <span className="text-destructive">{cs.late_payments}</span>
                          {" / "}
                          {cs.total_payments}
                        </p>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <Button variant="outline" size="sm">
                        View Full Report
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
