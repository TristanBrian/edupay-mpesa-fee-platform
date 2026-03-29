"use client";

import { useState } from "react";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Search, Phone, RefreshCw, CheckCircle, XCircle, Clock } from "lucide-react";
import { formatCurrency, formatDateTime, getStatusBadgeVariant } from "@/lib/utils";

interface Payment {
  id: number;
  payment_reference: string;
  invoice_number: string;
  student_name: string;
  amount: number;
  phone_number: string;
  mpesa_receipt: string | null;
  status: string;
  created_at: string;
}

// Demo data
const demoPayments: Payment[] = [
  { id: 1, payment_reference: "PAY-2024-001", invoice_number: "INV-001", student_name: "John Kamau", amount: 45000, phone_number: "+254712345678", mpesa_receipt: "QHK7B2XY1Z", status: "completed", created_at: "2024-03-15T10:30:00" },
  { id: 2, payment_reference: "PAY-2024-002", invoice_number: "INV-002", student_name: "Mary Wanjiku", amount: 32000, phone_number: "+254723456789", mpesa_receipt: "QHK7B2XY2Z", status: "completed", created_at: "2024-03-15T09:45:00" },
  { id: 3, payment_reference: "PAY-2024-003", invoice_number: "INV-003", student_name: "Peter Ochieng", amount: 15000, phone_number: "+254734567890", mpesa_receipt: null, status: "pending", created_at: "2024-03-15T09:15:00" },
  { id: 4, payment_reference: "PAY-2024-004", invoice_number: "INV-004", student_name: "Grace Muthoni", amount: 28000, phone_number: "+254745678901", mpesa_receipt: "QHK7B2XY3Z", status: "completed", created_at: "2024-03-14T16:20:00" },
  { id: 5, payment_reference: "PAY-2024-005", invoice_number: "INV-005", student_name: "David Kiprop", amount: 50000, phone_number: "+254756789012", mpesa_receipt: null, status: "failed", created_at: "2024-03-14T14:00:00" },
  { id: 6, payment_reference: "PAY-2024-006", invoice_number: "INV-006", student_name: "Lucy Wambui", amount: 22000, phone_number: "+254767890123", mpesa_receipt: null, status: "pending", created_at: "2024-03-14T12:30:00" },
];

const columns = [
  {
    key: "payment_reference",
    header: "Reference",
    cell: (payment: Payment) => (
      <span className="font-mono text-xs">{payment.payment_reference}</span>
    ),
  },
  {
    key: "student",
    header: "Student",
    cell: (payment: Payment) => (
      <div>
        <p className="font-medium">{payment.student_name}</p>
        <p className="text-xs text-muted-foreground">{payment.invoice_number}</p>
      </div>
    ),
  },
  {
    key: "amount",
    header: "Amount",
    cell: (payment: Payment) => (
      <span className="font-medium">{formatCurrency(payment.amount)}</span>
    ),
  },
  {
    key: "phone",
    header: "Phone",
    cell: (payment: Payment) => (
      <span className="text-sm">{payment.phone_number}</span>
    ),
  },
  {
    key: "receipt",
    header: "M-Pesa Receipt",
    cell: (payment: Payment) => (
      <span className="font-mono text-xs">
        {payment.mpesa_receipt || "-"}
      </span>
    ),
  },
  {
    key: "status",
    header: "Status",
    cell: (payment: Payment) => (
      <Badge variant={getStatusBadgeVariant(payment.status)}>
        {payment.status}
      </Badge>
    ),
  },
  {
    key: "created_at",
    header: "Date",
    cell: (payment: Payment) => (
      <span className="text-sm">{formatDateTime(payment.created_at)}</span>
    ),
  },
];

export default function PaymentsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isPayDialogOpen, setIsPayDialogOpen] = useState(false);
  const [paymentPhone, setPaymentPhone] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("");

  const filteredPayments = demoPayments.filter((payment) => {
    const matchesSearch =
      payment.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      payment.payment_reference.toLowerCase().includes(searchQuery.toLowerCase()) ||
      payment.invoice_number.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || payment.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalCompleted = demoPayments.filter(p => p.status === "completed").reduce((sum, p) => sum + p.amount, 0);
  const totalPending = demoPayments.filter(p => p.status === "pending").reduce((sum, p) => sum + p.amount, 0);
  const totalFailed = demoPayments.filter(p => p.status === "failed").reduce((sum, p) => sum + p.amount, 0);

  return (
    <div className="flex flex-col">
      <Header
        title="Payments"
        description="Manage M-Pesa payments and transactions"
      />

      <div className="flex-1 space-y-4 p-6">
        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Today</CardTitle>
              <CheckCircle className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(totalCompleted)}</div>
              <p className="text-xs text-muted-foreground">
                {demoPayments.filter(p => p.status === "completed").length} transactions
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
                {demoPayments.filter(p => p.status === "pending").length} awaiting confirmation
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
                {demoPayments.filter(p => p.status === "failed").length} failed transactions
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <RefreshCw className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {((demoPayments.filter(p => p.status === "completed").length / demoPayments.length) * 100).toFixed(1)}%
              </div>
              <p className="text-xs text-muted-foreground">
                {demoPayments.length} total transactions
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
                placeholder="Search payments..."
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
          </div>

          <Dialog open={isPayDialogOpen} onOpenChange={setIsPayDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Initiate Payment
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
              <DialogHeader>
                <DialogTitle>Initiate M-Pesa Payment</DialogTitle>
                <DialogDescription>
                  Send an STK push to the payer&apos;s phone for instant payment.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="invoice">Select Invoice</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select an invoice" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">INV-001 - John Kamau (KES 30,000)</SelectItem>
                      <SelectItem value="2">INV-003 - Peter Ochieng (KES 40,000)</SelectItem>
                      <SelectItem value="3">INV-005 - David Kiprop (KES 52,000)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="phone">Phone Number</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="phone"
                      placeholder="+254712345678"
                      value={paymentPhone}
                      onChange={(e) => setPaymentPhone(e.target.value)}
                      className="pl-9"
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="amount">Amount (KES)</Label>
                  <Input
                    id="amount"
                    type="number"
                    placeholder="Enter amount"
                    value={paymentAmount}
                    onChange={(e) => setPaymentAmount(e.target.value)}
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsPayDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsPayDialogOpen(false)}>
                  Send STK Push
                </Button>
              </DialogFooter>
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
