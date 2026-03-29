"use client";

import { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { DataTable } from "@/components/ui/data-table";
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
import { 
  Plus, 
  Search, 
  Phone, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  Clock,
  Loader2,
  Smartphone,
  AlertCircle
} from "lucide-react";
import { formatCurrency, formatDateTime, getStatusBadgeVariant } from "@/lib/utils";
import { paymentsApi, type PaymentRecord, type PaymentInitiateResponse, type PaymentStatusResponse } from "@/lib/api";

// Demo data for offline/initial state
const demoPayments: PaymentRecord[] = [
  { 
    id: 1, 
    transaction_id: "TXN8A2B4C6D8E0", 
    checkout_request_id: "ws_CO_20240315103000001",
    amount: 45000, 
    phone: "254712345678", 
    account_reference: "INV-001",
    mpesa_receipt_number: "QHK7B2XY1Z", 
    status: "completed", 
    created_at: "2024-03-15T10:30:00",
    completed_at: "2024-03-15T10:31:00"
  },
  { 
    id: 2, 
    transaction_id: "TXN1F3G5H7I9K1", 
    checkout_request_id: "ws_CO_20240315094500002",
    amount: 32000, 
    phone: "254723456789", 
    account_reference: "INV-002",
    mpesa_receipt_number: "QHK7B2XY2Z", 
    status: "completed", 
    created_at: "2024-03-15T09:45:00",
    completed_at: "2024-03-15T09:46:30"
  },
  { 
    id: 3, 
    transaction_id: "TXN2L4M6N8O0P2", 
    checkout_request_id: "ws_CO_20240315091500003",
    amount: 15000, 
    phone: "254734567890", 
    account_reference: "INV-003",
    status: "pending", 
    created_at: "2024-03-15T09:15:00"
  },
  { 
    id: 4, 
    transaction_id: "TXN3Q5R7S9T1U3", 
    checkout_request_id: "ws_CO_20240314162000004",
    amount: 28000, 
    phone: "254745678901", 
    account_reference: "INV-004",
    mpesa_receipt_number: "QHK7B2XY3Z", 
    status: "completed", 
    created_at: "2024-03-14T16:20:00",
    completed_at: "2024-03-14T16:21:15"
  },
  { 
    id: 5, 
    transaction_id: "TXN4V6W8X0Y2Z4", 
    checkout_request_id: "ws_CO_20240314140000005",
    amount: 50000, 
    phone: "254756789012", 
    account_reference: "INV-005",
    status: "failed", 
    result_code: "1032",
    result_desc: "Request cancelled by user",
    created_at: "2024-03-14T14:00:00"
  },
];

const columns = [
  {
    key: "transaction_id",
    header: "Transaction ID",
    cell: (payment: PaymentRecord) => (
      <span className="font-mono text-xs">{payment.transaction_id}</span>
    ),
  },
  {
    key: "account_reference",
    header: "Reference",
    cell: (payment: PaymentRecord) => (
      <span className="text-sm">{payment.account_reference || "-"}</span>
    ),
  },
  {
    key: "amount",
    header: "Amount",
    cell: (payment: PaymentRecord) => (
      <span className="font-medium">{formatCurrency(payment.amount)}</span>
    ),
  },
  {
    key: "phone",
    header: "Phone",
    cell: (payment: PaymentRecord) => (
      <span className="text-sm font-mono">{payment.phone}</span>
    ),
  },
  {
    key: "receipt",
    header: "M-Pesa Receipt",
    cell: (payment: PaymentRecord) => (
      <span className="font-mono text-xs">
        {payment.mpesa_receipt_number || "-"}
      </span>
    ),
  },
  {
    key: "status",
    header: "Status",
    cell: (payment: PaymentRecord) => (
      <Badge variant={getStatusBadgeVariant(payment.status)}>
        {payment.status}
      </Badge>
    ),
  },
  {
    key: "created_at",
    header: "Date",
    cell: (payment: PaymentRecord) => (
      <span className="text-sm">{formatDateTime(payment.created_at)}</span>
    ),
  },
];

type PaymentStep = "form" | "processing" | "polling" | "result";

interface PaymentState {
  step: PaymentStep;
  transactionId?: string;
  checkoutId?: string;
  result?: PaymentStatusResponse;
  error?: string;
}

export default function PaymentsPage() {
  const [payments, setPayments] = useState<PaymentRecord[]>(demoPayments);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isPayDialogOpen, setIsPayDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  // Payment form state
  const [paymentPhone, setPaymentPhone] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [accountReference, setAccountReference] = useState("");
  
  // Payment flow state
  const [paymentState, setPaymentState] = useState<PaymentState>({ step: "form" });
  
  // Polling interval ref
  const [pollingCount, setPollingCount] = useState(0);
  const MAX_POLLS = 30; // Poll for ~60 seconds (2s interval)

  // Fetch payments from API
  useEffect(() => {
    const fetchPayments = async () => {
      try {
        const data = await paymentsApi.list();
        if (data && data.length > 0) {
          setPayments(data);
        }
      } catch (error) {
        console.log("[v0] Using demo data - API not available:", error);
      }
    };
    fetchPayments();
  }, []);

  // Polling for payment status
  useEffect(() => {
    if (paymentState.step !== "polling" || !paymentState.transactionId) {
      return;
    }

    if (pollingCount >= MAX_POLLS) {
      setPaymentState({
        ...paymentState,
        step: "result",
        error: "Payment confirmation timed out. Please check your M-Pesa messages or try again."
      });
      return;
    }

    const pollStatus = async () => {
      try {
        const status = await paymentsApi.getStatus(paymentState.transactionId!);
        
        if (status.status === "completed") {
          setPaymentState({
            step: "result",
            transactionId: paymentState.transactionId,
            checkoutId: paymentState.checkoutId,
            result: status
          });
          // Refresh payments list
          refreshPayments();
        } else if (status.status === "failed") {
          setPaymentState({
            step: "result",
            transactionId: paymentState.transactionId,
            checkoutId: paymentState.checkoutId,
            result: status,
            error: status.result_desc || "Payment failed"
          });
        } else {
          // Still pending, increment poll count
          setPollingCount(prev => prev + 1);
        }
      } catch (error) {
        console.log("[v0] Polling error:", error);
        setPollingCount(prev => prev + 1);
      }
    };

    const timer = setTimeout(pollStatus, 2000);
    return () => clearTimeout(timer);
  }, [paymentState, pollingCount]);

  const refreshPayments = async () => {
    try {
      const data = await paymentsApi.list();
      if (data && data.length > 0) {
        setPayments(data);
      }
    } catch (error) {
      console.log("[v0] Error refreshing payments:", error);
    }
  };

  const handleInitiatePayment = async () => {
    // Validate inputs
    if (!paymentPhone || !paymentAmount) {
      setPaymentState({ step: "form", error: "Please fill in all required fields" });
      return;
    }

    const amount = parseInt(paymentAmount);
    if (isNaN(amount) || amount < 1 || amount > 150000) {
      setPaymentState({ step: "form", error: "Amount must be between 1 and 150,000 KES" });
      return;
    }

    setPaymentState({ step: "processing" });
    setIsLoading(true);

    try {
      const response = await paymentsApi.initiate({
        amount,
        phone: paymentPhone,
        account_reference: accountReference || `PAY-${Date.now()}`,
        transaction_desc: "School Fee Payment"
      });

      if (response.success) {
        setPaymentState({
          step: "polling",
          transactionId: response.transaction_id,
          checkoutId: response.checkout_id
        });
        setPollingCount(0);
      } else {
        setPaymentState({
          step: "result",
          error: response.message || "Failed to initiate payment"
        });
      }
    } catch (error) {
      console.log("[v0] Payment initiation error:", error);
      setPaymentState({
        step: "result",
        error: error instanceof Error ? error.message : "Failed to initiate payment"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSimulateSuccess = async () => {
    if (!paymentState.checkoutId) return;
    
    try {
      await paymentsApi.simulateCallback(paymentState.checkoutId, true);
      // The polling will pick up the status change
    } catch (error) {
      console.log("[v0] Simulate error:", error);
    }
  };

  const handleCloseDialog = () => {
    setIsPayDialogOpen(false);
    setPaymentState({ step: "form" });
    setPaymentPhone("");
    setPaymentAmount("");
    setAccountReference("");
    setPollingCount(0);
    refreshPayments();
  };

  const handleNewPayment = () => {
    setPaymentState({ step: "form" });
    setPaymentPhone("");
    setPaymentAmount("");
    setAccountReference("");
    setPollingCount(0);
  };

  const filteredPayments = payments.filter((payment) => {
    const matchesSearch =
      payment.transaction_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      payment.phone.includes(searchQuery) ||
      (payment.account_reference?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
      (payment.mpesa_receipt_number?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
    const matchesStatus = statusFilter === "all" || payment.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalCompleted = payments.filter(p => p.status === "completed").reduce((sum, p) => sum + p.amount, 0);
  const totalPending = payments.filter(p => p.status === "pending").reduce((sum, p) => sum + p.amount, 0);
  const totalFailed = payments.filter(p => p.status === "failed").reduce((sum, p) => sum + p.amount, 0);
  const successRate = payments.length > 0 
    ? (payments.filter(p => p.status === "completed").length / payments.length) * 100 
    : 0;

  return (
    <div className="flex flex-col">
      <Header
        title="Payments"
        description="Manage M-Pesa STK Push payments and transactions"
      />

      <div className="flex-1 space-y-4 p-6">
        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <CheckCircle className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(totalCompleted)}</div>
              <p className="text-xs text-muted-foreground">
                {payments.filter(p => p.status === "completed").length} successful payments
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending</CardTitle>
              <Clock className="h-4 w-4 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-warning">{formatCurrency(totalPending)}</div>
              <p className="text-xs text-muted-foreground">
                {payments.filter(p => p.status === "pending").length} awaiting confirmation
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed</CardTitle>
              <XCircle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">{formatCurrency(totalFailed)}</div>
              <p className="text-xs text-muted-foreground">
                {payments.filter(p => p.status === "failed").length} failed transactions
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <RefreshCw className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{successRate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                {payments.length} total transactions
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Actions */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by phone, reference, receipt..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={refreshPayments}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>

          <Dialog open={isPayDialogOpen} onOpenChange={setIsPayDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                New STK Push
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[450px]">
              {paymentState.step === "form" && (
                <>
                  <DialogHeader>
                    <DialogTitle>Initiate M-Pesa Payment</DialogTitle>
                    <DialogDescription>
                      Send an STK Push request to collect payment via M-Pesa.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="grid gap-4 py-4">
                    {paymentState.error && (
                      <div className="flex items-center gap-2 p-3 text-sm text-destructive bg-destructive/10 rounded-lg">
                        <AlertCircle className="h-4 w-4" />
                        {paymentState.error}
                      </div>
                    )}
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone Number *</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input
                          id="phone"
                          placeholder="0712345678 or 254712345678"
                          value={paymentPhone}
                          onChange={(e) => setPaymentPhone(e.target.value)}
                          className="pl-9"
                        />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Safaricom number to receive STK Push
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="amount">Amount (KES) *</Label>
                      <Input
                        id="amount"
                        type="number"
                        placeholder="Enter amount (1 - 150,000)"
                        value={paymentAmount}
                        onChange={(e) => setPaymentAmount(e.target.value)}
                        min={1}
                        max={150000}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="reference">Account Reference</Label>
                      <Input
                        id="reference"
                        placeholder="e.g., INV-001 or Student ID"
                        value={accountReference}
                        onChange={(e) => setAccountReference(e.target.value)}
                      />
                      <p className="text-xs text-muted-foreground">
                        This will appear in the M-Pesa message
                      </p>
                    </div>
                  </div>
                  <DialogFooter>
                    <Button variant="outline" onClick={handleCloseDialog}>
                      Cancel
                    </Button>
                    <Button onClick={handleInitiatePayment} disabled={isLoading}>
                      {isLoading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Smartphone className="h-4 w-4 mr-2" />
                          Send STK Push
                        </>
                      )}
                    </Button>
                  </DialogFooter>
                </>
              )}

              {paymentState.step === "processing" && (
                <div className="py-12 text-center">
                  <Loader2 className="h-12 w-12 mx-auto mb-4 animate-spin text-primary" />
                  <h3 className="text-lg font-medium mb-2">Sending STK Push</h3>
                  <p className="text-sm text-muted-foreground">
                    Please wait while we send the payment request...
                  </p>
                </div>
              )}

              {paymentState.step === "polling" && (
                <div className="py-8 text-center">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
                    <Smartphone className="h-8 w-8 text-primary animate-pulse" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">Check Your Phone</h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    An M-Pesa prompt has been sent to <strong>{paymentPhone}</strong>
                  </p>
                  <p className="text-sm text-muted-foreground mb-6">
                    Enter your M-Pesa PIN to complete the payment of{" "}
                    <strong>{formatCurrency(parseInt(paymentAmount))}</strong>
                  </p>
                  
                  <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mb-4">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Waiting for confirmation... ({pollingCount}/{MAX_POLLS})
                  </div>

                  <div className="space-y-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleSimulateSuccess}
                      className="w-full"
                    >
                      Simulate Success (Mock Mode)
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCloseDialog}
                      className="w-full"
                    >
                      Close and Check Later
                    </Button>
                  </div>
                </div>
              )}

              {paymentState.step === "result" && (
                <div className="py-8 text-center">
                  {paymentState.error ? (
                    <>
                      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-destructive/10 flex items-center justify-center">
                        <XCircle className="h-8 w-8 text-destructive" />
                      </div>
                      <h3 className="text-lg font-medium mb-2">Payment Failed</h3>
                      <p className="text-sm text-muted-foreground mb-6">
                        {paymentState.error}
                      </p>
                    </>
                  ) : (
                    <>
                      <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-success/10 flex items-center justify-center">
                        <CheckCircle className="h-8 w-8 text-success" />
                      </div>
                      <h3 className="text-lg font-medium mb-2">Payment Successful</h3>
                      <p className="text-sm text-muted-foreground mb-2">
                        {formatCurrency(parseInt(paymentAmount))} received
                      </p>
                      {paymentState.result?.mpesa_receipt && (
                        <p className="text-sm font-mono mb-6">
                          Receipt: {paymentState.result.mpesa_receipt}
                        </p>
                      )}
                    </>
                  )}
                  
                  <div className="space-y-2">
                    <Button onClick={handleNewPayment} className="w-full">
                      New Payment
                    </Button>
                    <Button variant="outline" onClick={handleCloseDialog} className="w-full">
                      Close
                    </Button>
                  </div>
                </div>
              )}
            </DialogContent>
          </Dialog>
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredPayments}
          keyExtractor={(payment) => payment.id}
          emptyMessage="No payments found"
        />
      </div>
    </div>
  );
}
