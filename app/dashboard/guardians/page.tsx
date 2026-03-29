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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, Search, Users, Phone, CreditCard } from "lucide-react";
import { formatCurrency } from "@/lib/utils";

interface Guardian {
  id: number;
  first_name: string;
  last_name: string;
  phone: string;
  email: string;
  id_number: string;
  students: number;
  total_balance: number;
  credit_score: number;
  status: string;
}

// Demo data
const demoGuardians: Guardian[] = [
  { id: 1, first_name: "James", last_name: "Kamau", phone: "+254712345678", email: "james.kamau@email.com", id_number: "12345678", students: 2, total_balance: 30000, credit_score: 720, status: "active" },
  { id: 2, first_name: "Jane", last_name: "Wanjiku", phone: "+254723456789", email: "jane.wanjiku@email.com", id_number: "23456789", students: 1, total_balance: 0, credit_score: 800, status: "active" },
  { id: 3, first_name: "Paul", last_name: "Ochieng", phone: "+254734567890", email: "paul.ochieng@email.com", id_number: "34567890", students: 1, total_balance: 40000, credit_score: 580, status: "active" },
  { id: 4, first_name: "George", last_name: "Muthoni", phone: "+254745678901", email: "george.muthoni@email.com", id_number: "45678901", students: 1, total_balance: 0, credit_score: 750, status: "active" },
  { id: 5, first_name: "Daniel", last_name: "Kiprop", phone: "+254756789012", email: "daniel.kiprop@email.com", id_number: "56789012", students: 1, total_balance: 52000, credit_score: 450, status: "at_risk" },
];

function getCreditScoreVariant(score: number): "success" | "warning" | "destructive" {
  if (score >= 700) return "success";
  if (score >= 550) return "warning";
  return "destructive";
}

const columns = [
  {
    key: "name",
    header: "Guardian",
    cell: (guardian: Guardian) => (
      <div>
        <p className="font-medium">{guardian.first_name} {guardian.last_name}</p>
        <p className="text-xs text-muted-foreground">ID: {guardian.id_number}</p>
      </div>
    ),
  },
  {
    key: "contact",
    header: "Contact",
    cell: (guardian: Guardian) => (
      <div>
        <p className="text-sm">{guardian.phone}</p>
        <p className="text-xs text-muted-foreground">{guardian.email}</p>
      </div>
    ),
  },
  {
    key: "students",
    header: "Students",
    cell: (guardian: Guardian) => (
      <span className="font-medium">{guardian.students}</span>
    ),
  },
  {
    key: "balance",
    header: "Outstanding",
    cell: (guardian: Guardian) => (
      <span className={guardian.total_balance > 0 ? "text-destructive font-medium" : "text-success font-medium"}>
        {formatCurrency(guardian.total_balance)}
      </span>
    ),
  },
  {
    key: "credit_score",
    header: "Credit Score",
    cell: (guardian: Guardian) => (
      <Badge variant={getCreditScoreVariant(guardian.credit_score)}>
        {guardian.credit_score}
      </Badge>
    ),
  },
  {
    key: "status",
    header: "Status",
    cell: (guardian: Guardian) => (
      <Badge variant={guardian.status === "active" ? "success" : "warning"}>
        {guardian.status}
      </Badge>
    ),
  },
];

export default function GuardiansPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

  const filteredGuardians = demoGuardians.filter((guardian) =>
    guardian.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    guardian.last_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    guardian.phone.includes(searchQuery)
  );

  const totalGuardians = demoGuardians.length;
  const totalStudents = demoGuardians.reduce((sum, g) => sum + g.students, 0);
  const totalOutstanding = demoGuardians.reduce((sum, g) => sum + g.total_balance, 0);
  const avgCreditScore = Math.round(demoGuardians.reduce((sum, g) => sum + g.credit_score, 0) / demoGuardians.length);

  return (
    <div className="flex flex-col">
      <Header
        title="Guardians"
        description="Manage parent and guardian records"
      />

      <div className="flex-1 space-y-4 p-6">
        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Guardians</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalGuardians}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Students Linked</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalStudents}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Outstanding</CardTitle>
              <Phone className="h-4 w-4 text-warning" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-warning">{formatCurrency(totalOutstanding)}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Credit Score</CardTitle>
              <CreditCard className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgCreditScore}</div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Actions */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search guardians..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Guardian
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Add New Guardian</DialogTitle>
                <DialogDescription>
                  Register a new parent or guardian.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input id="firstName" placeholder="James" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input id="lastName" placeholder="Kamau" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone Number</Label>
                    <Input id="phone" placeholder="+254712345678" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" placeholder="james@email.com" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="idNumber">ID Number</Label>
                  <Input id="idNumber" placeholder="12345678" />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsAddDialogOpen(false)}>
                  Add Guardian
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredGuardians}
          keyExtractor={(guardian) => guardian.id}
          emptyMessage="No guardians found"
        />
      </div>
    </div>
  );
}
