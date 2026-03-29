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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Search, FileText, CreditCard, AlertTriangle } from "lucide-react";
import { formatCurrency, formatDate, getStatusBadgeVariant } from "@/lib/utils";
import Link from "next/link";

interface Invoice {
  id: number;
  invoice_number: string;
  student_name: string;
  admission_number: string;
  school_name: string;
  amount: number;
  paid_amount: number;
  balance: number;
  due_date: string;
  term: string;
  academic_year: string;
  status: string;
  created_at: string;
}

// Demo data
const demoInvoices: Invoice[] = [
  { id: 1, invoice_number: "INV-2024-001", student_name: "John Kamau", admission_number: "ADM-001", school_name: "Starehe Boys", amount: 75000, paid_amount: 45000, balance: 30000, due_date: "2024-04-30", term: "Term 1", academic_year: "2024", status: "partial", created_at: "2024-01-15" },
  { id: 2, invoice_number: "INV-2024-002", student_name: "Mary Wanjiku", admission_number: "ADM-002", school_name: "Alliance Girls", amount: 65000, paid_amount: 65000, balance: 0, due_date: "2024-04-30", term: "Term 1", academic_year: "2024", status: "paid", created_at: "2024-01-15" },
  { id: 3, invoice_number: "INV-2024-003", student_name: "Peter Ochieng", admission_number: "ADM-003", school_name: "Maseno School", amount: 80000, paid_amount: 40000, balance: 40000, due_date: "2024-03-15", term: "Term 1", academic_year: "2024", status: "overdue", created_at: "2024-01-16" },
  { id: 4, invoice_number: "INV-2024-004", student_name: "Grace Muthoni", admission_number: "ADM-004", school_name: "Kenya High", amount: 70000, paid_amount: 70000, balance: 0, due_date: "2024-04-30", term: "Term 1", academic_year: "2024", status: "paid", created_at: "2024-01-17" },
  { id: 5, invoice_number: "INV-2024-005", student_name: "David Kiprop", admission_number: "ADM-005", school_name: "Moi Forces", amount: 72000, paid_amount: 20000, balance: 52000, due_date: "2024-03-01", term: "Term 1", academic_year: "2024", status: "overdue", created_at: "2024-01-18" },
  { id: 6, invoice_number: "INV-2024-006", student_name: "Lucy Wambui", admission_number: "ADM-006", school_name: "Loreto High", amount: 68000, paid_amount: 0, balance: 68000, due_date: "2024-05-15", term: "Term 1", academic_year: "2024", status: "pending", created_at: "2024-01-20" },
];

const columns = [
  {
    key: "invoice_number",
    header: "Invoice",
    cell: (invoice: Invoice) => (
      <span className="font-mono text-xs">{invoice.invoice_number}</span>
    ),
  },
  {
    key: "student",
    header: "Student",
    cell: (invoice: Invoice) => (
      <div>
        <p className="font-medium">{invoice.student_name}</p>
        <p className="text-xs text-muted-foreground">{invoice.admission_number}</p>
      </div>
    ),
  },
  {
    key: "school",
    header: "School",
    cell: (invoice: Invoice) => invoice.school_name,
  },
  {
    key: "amount",
    header: "Amount",
    cell: (invoice: Invoice) => (
      <div>
        <p className="font-medium">{formatCurrency(invoice.amount)}</p>
        <p className="text-xs text-muted-foreground">
          Paid: {formatCurrency(invoice.paid_amount)}
        </p>
      </div>
    ),
  },
  {
    key: "balance",
    header: "Balance",
    cell: (invoice: Invoice) => (
      <span className={invoice.balance > 0 ? "text-destructive font-medium" : "text-success font-medium"}>
        {formatCurrency(invoice.balance)}
      </span>
    ),
  },
  {
    key: "due_date",
    header: "Due Date",
    cell: (invoice: Invoice) => (
      <span className="text-sm">{formatDate(invoice.due_date)}</span>
    ),
  },
  {
    key: "status",
    header: "Status",
    cell: (invoice: Invoice) => (
      <Badge variant={getStatusBadgeVariant(invoice.status)}>
        {invoice.status}
      </Badge>
    ),
  },
  {
    key: "actions",
    header: "Actions",
    cell: (invoice: Invoice) => (
      <Link href={`/dashboard/payments?invoice=${invoice.id}`}>
        <Button variant="ghost" size="sm">
          <CreditCard className="h-4 w-4 mr-1" />
          Pay
        </Button>
      </Link>
    ),
  },
];

export default function InvoicesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const filteredInvoices = demoInvoices.filter((invoice) => {
    const matchesSearch =
      invoice.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      invoice.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      invoice.admission_number.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || invoice.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const totalInvoiced = demoInvoices.reduce((sum, i) => sum + i.amount, 0);
  const totalPaid = demoInvoices.reduce((sum, i) => sum + i.paid_amount, 0);
  const totalOutstanding = demoInvoices.reduce((sum, i) => sum + i.balance, 0);
  const overdueCount = demoInvoices.filter(i => i.status === "overdue").length;

  return (
    <div className="flex flex-col">
      <Header
        title="Invoices"
        description="Manage student fee invoices"
      />

      <div className="flex-1 space-y-4 p-6">
        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Invoiced</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(totalInvoiced)}</div>
              <p className="text-xs text-muted-foreground">{demoInvoices.length} invoices</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Paid</CardTitle>
              <CreditCard className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-success">{formatCurrency(totalPaid)}</div>
              <p className="text-xs text-muted-foreground">
                {((totalPaid / totalInvoiced) * 100).toFixed(1)}% collected
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Outstanding</CardTitle>
              <AlertTriangle className="h-4 w-4 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-warning">{formatCurrency(totalOutstanding)}</div>
              <p className="text-xs text-muted-foreground">
                {demoInvoices.filter(i => i.balance > 0).length} pending
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overdue</CardTitle>
              <AlertTriangle className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">{overdueCount}</div>
              <p className="text-xs text-muted-foreground">Need attention</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Actions */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search invoices..."
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
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="partial">Partial</SelectItem>
                <SelectItem value="paid">Paid</SelectItem>
                <SelectItem value="overdue">Overdue</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Invoice
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Create Invoice</DialogTitle>
                <DialogDescription>
                  Generate a new fee invoice for a student.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label>Select Student</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a student" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">John Kamau (ADM-001)</SelectItem>
                      <SelectItem value="2">Mary Wanjiku (ADM-002)</SelectItem>
                      <SelectItem value="3">Peter Ochieng (ADM-003)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Term</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select term" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="term1">Term 1</SelectItem>
                        <SelectItem value="term2">Term 2</SelectItem>
                        <SelectItem value="term3">Term 3</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Academic Year</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select year" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="2024">2024</SelectItem>
                        <SelectItem value="2025">2025</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Amount (KES)</Label>
                  <Input type="number" placeholder="Enter fee amount" />
                </div>
                <div className="space-y-2">
                  <Label>Due Date</Label>
                  <Input type="date" />
                </div>
                <div className="space-y-2">
                  <Label>Description (Optional)</Label>
                  <Input placeholder="e.g., School fees for Term 1" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsCreateDialogOpen(false)}>
                  Create Invoice
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredInvoices}
          keyExtractor={(invoice) => invoice.id}
          emptyMessage="No invoices found"
        />
      </div>
    </div>
  );
}
