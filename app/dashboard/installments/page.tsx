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
import { Plus, Search, Calendar, CreditCard, ChevronRight } from "lucide-react";
import { formatCurrency, formatDate, getStatusBadgeVariant } from "@/lib/utils";

interface InstallmentPlan {
  id: number;
  plan_number: string;
  student_name: string;
  admission_number: string;
  total_amount: number;
  paid_amount: number;
  remaining_amount: number;
  number_of_installments: number;
  paid_installments: number;
  frequency: string;
  start_date: string;
  next_due_date: string;
  next_amount: number;
  status: string;
}

// Demo data
const demoPlans: InstallmentPlan[] = [
  { id: 1, plan_number: "PLN-001", student_name: "John Kamau", admission_number: "ADM-001", total_amount: 75000, paid_amount: 25000, remaining_amount: 50000, number_of_installments: 3, paid_installments: 1, frequency: "monthly", start_date: "2024-01-15", next_due_date: "2024-04-15", next_amount: 25000, status: "active" },
  { id: 2, plan_number: "PLN-002", student_name: "Peter Ochieng", admission_number: "ADM-003", total_amount: 80000, paid_amount: 40000, remaining_amount: 40000, number_of_installments: 4, paid_installments: 2, frequency: "monthly", start_date: "2024-01-20", next_due_date: "2024-04-20", next_amount: 20000, status: "active" },
  { id: 3, plan_number: "PLN-003", student_name: "David Kiprop", admission_number: "ADM-005", total_amount: 72000, paid_amount: 0, remaining_amount: 72000, number_of_installments: 4, paid_installments: 0, frequency: "monthly", start_date: "2024-02-01", next_due_date: "2024-03-01", next_amount: 18000, status: "overdue" },
  { id: 4, plan_number: "PLN-004", student_name: "Faith Akinyi", admission_number: "ADM-006", total_amount: 65000, paid_amount: 65000, remaining_amount: 0, number_of_installments: 3, paid_installments: 3, frequency: "monthly", start_date: "2023-11-01", next_due_date: "-", next_amount: 0, status: "completed" },
];

export default function InstallmentsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const filteredPlans = demoPlans.filter((plan) => {
    const matchesSearch =
      plan.student_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plan.plan_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      plan.admission_number.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || plan.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const activePlans = demoPlans.filter(p => p.status === "active").length;
  const overduePlans = demoPlans.filter(p => p.status === "overdue").length;
  const totalOutstanding = demoPlans.reduce((sum, p) => sum + p.remaining_amount, 0);
  const completedPlans = demoPlans.filter(p => p.status === "completed").length;

  return (
    <div className="flex flex-col">
      <Header
        title="Installment Plans"
        description="Manage flexible fee payment plans"
      />

      <div className="flex-1 space-y-4 p-6">
        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Plans</CardTitle>
              <Calendar className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activePlans}</div>
              <p className="text-xs text-muted-foreground">Currently running</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Overdue</CardTitle>
              <Calendar className="h-4 w-4 text-destructive" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-destructive">{overduePlans}</div>
              <p className="text-xs text-muted-foreground">Need attention</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Outstanding</CardTitle>
              <CreditCard className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(totalOutstanding)}</div>
              <p className="text-xs text-muted-foreground">Remaining balance</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Completed</CardTitle>
              <Calendar className="h-4 w-4 text-success" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-success">{completedPlans}</div>
              <p className="text-xs text-muted-foreground">Fully paid</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Actions */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search plans..."
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
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="overdue">Overdue</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Create Plan
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Create Installment Plan</DialogTitle>
                <DialogDescription>
                  Set up a flexible payment plan for an invoice.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="space-y-2">
                  <Label>Select Invoice</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select an invoice" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">INV-001 - John Kamau (KES 75,000)</SelectItem>
                      <SelectItem value="2">INV-003 - Peter Ochieng (KES 80,000)</SelectItem>
                      <SelectItem value="3">INV-005 - David Kiprop (KES 72,000)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Number of Installments</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="2">2 Installments</SelectItem>
                        <SelectItem value="3">3 Installments</SelectItem>
                        <SelectItem value="4">4 Installments</SelectItem>
                        <SelectItem value="6">6 Installments</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Frequency</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Select" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="weekly">Weekly</SelectItem>
                        <SelectItem value="bi-weekly">Bi-Weekly</SelectItem>
                        <SelectItem value="monthly">Monthly</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Start Date</Label>
                  <Input type="date" />
                </div>
                <div className="rounded-lg border bg-muted/50 p-4">
                  <p className="text-sm font-medium mb-2">Plan Summary</p>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total Amount:</span>
                      <span className="font-medium">KES 75,000</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Per Installment:</span>
                      <span className="font-medium">KES 25,000</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Duration:</span>
                      <span className="font-medium">3 months</span>
                    </div>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsCreateDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsCreateDialogOpen(false)}>
                  Create Plan
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Plans List */}
        <div className="grid gap-4">
          {filteredPlans.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">No installment plans found</p>
              </CardContent>
            </Card>
          ) : (
            filteredPlans.map((plan) => (
              <Card key={plan.id} className="hover:bg-accent/50 transition-colors cursor-pointer">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 space-y-3">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-sm text-muted-foreground">{plan.plan_number}</span>
                        <Badge variant={getStatusBadgeVariant(plan.status)}>
                          {plan.status}
                        </Badge>
                      </div>
                      
                      <div>
                        <h3 className="font-semibold">{plan.student_name}</h3>
                        <p className="text-sm text-muted-foreground">{plan.admission_number}</p>
                      </div>

                      <div className="flex items-center gap-6 text-sm">
                        <div>
                          <span className="text-muted-foreground">Total: </span>
                          <span className="font-medium">{formatCurrency(plan.total_amount)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Paid: </span>
                          <span className="font-medium text-success">{formatCurrency(plan.paid_amount)}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Remaining: </span>
                          <span className="font-medium text-destructive">{formatCurrency(plan.remaining_amount)}</span>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">
                            Progress: {plan.paid_installments}/{plan.number_of_installments} installments
                          </span>
                          <span className="font-medium">
                            {Math.round((plan.paid_amount / plan.total_amount) * 100)}%
                          </span>
                        </div>
                        <Progress value={(plan.paid_amount / plan.total_amount) * 100} />
                      </div>
                    </div>

                    <div className="ml-6 flex flex-col items-end gap-2">
                      {plan.status !== "completed" && (
                        <div className="text-right">
                          <p className="text-sm text-muted-foreground">Next Payment</p>
                          <p className="font-medium">{formatCurrency(plan.next_amount)}</p>
                          <p className="text-xs text-muted-foreground">Due: {formatDate(plan.next_due_date)}</p>
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
      </div>
    </div>
  );
}
