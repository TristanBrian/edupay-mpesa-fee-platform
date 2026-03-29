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
import { Plus, Search, Eye } from "lucide-react";
import { formatCurrency, formatDate, getStatusBadgeVariant } from "@/lib/utils";
import Link from "next/link";

interface Student {
  id: number;
  admission_number: string;
  first_name: string;
  last_name: string;
  grade: string;
  status: string;
  school_name: string;
  guardian_name: string;
  guardian_phone: string;
  total_fees: number;
  paid_amount: number;
  balance: number;
  created_at: string;
}

// Demo data
const demoStudents: Student[] = [
  { id: 1, admission_number: "ADM-2024-001", first_name: "John", last_name: "Kamau", grade: "Form 3", status: "active", school_name: "Starehe Boys", guardian_name: "James Kamau", guardian_phone: "+254712345678", total_fees: 75000, paid_amount: 45000, balance: 30000, created_at: "2024-01-15" },
  { id: 2, admission_number: "ADM-2024-002", first_name: "Mary", last_name: "Wanjiku", grade: "Form 2", status: "active", school_name: "Alliance Girls", guardian_name: "Jane Wanjiku", guardian_phone: "+254723456789", total_fees: 65000, paid_amount: 65000, balance: 0, created_at: "2024-01-15" },
  { id: 3, admission_number: "ADM-2024-003", first_name: "Peter", last_name: "Ochieng", grade: "Form 4", status: "active", school_name: "Maseno School", guardian_name: "Paul Ochieng", guardian_phone: "+254734567890", total_fees: 80000, paid_amount: 40000, balance: 40000, created_at: "2024-01-16" },
  { id: 4, admission_number: "ADM-2024-004", first_name: "Grace", last_name: "Muthoni", grade: "Form 1", status: "active", school_name: "Kenya High", guardian_name: "George Muthoni", guardian_phone: "+254745678901", total_fees: 70000, paid_amount: 70000, balance: 0, created_at: "2024-01-17" },
  { id: 5, admission_number: "ADM-2024-005", first_name: "David", last_name: "Kiprop", grade: "Form 3", status: "suspended", school_name: "Moi Forces", guardian_name: "Daniel Kiprop", guardian_phone: "+254756789012", total_fees: 72000, paid_amount: 20000, balance: 52000, created_at: "2024-01-18" },
];

const demoSchools = [
  { id: 1, name: "Starehe Boys" },
  { id: 2, name: "Alliance Girls" },
  { id: 3, name: "Maseno School" },
  { id: 4, name: "Kenya High" },
  { id: 5, name: "Moi Forces" },
];

const columns = [
  {
    key: "admission_number",
    header: "Admission No.",
    cell: (student: Student) => (
      <span className="font-mono text-xs">{student.admission_number}</span>
    ),
  },
  {
    key: "name",
    header: "Student Name",
    cell: (student: Student) => (
      <div>
        <p className="font-medium">{student.first_name} {student.last_name}</p>
        <p className="text-xs text-muted-foreground">{student.grade}</p>
      </div>
    ),
  },
  {
    key: "school",
    header: "School",
    cell: (student: Student) => student.school_name,
  },
  {
    key: "guardian",
    header: "Guardian",
    cell: (student: Student) => (
      <div>
        <p className="text-sm">{student.guardian_name}</p>
        <p className="text-xs text-muted-foreground">{student.guardian_phone}</p>
      </div>
    ),
  },
  {
    key: "fees",
    header: "Fees Status",
    cell: (student: Student) => (
      <div>
        <p className="text-sm font-medium">{formatCurrency(student.paid_amount)} / {formatCurrency(student.total_fees)}</p>
        <p className={`text-xs ${student.balance > 0 ? 'text-destructive' : 'text-success'}`}>
          Balance: {formatCurrency(student.balance)}
        </p>
      </div>
    ),
  },
  {
    key: "status",
    header: "Status",
    cell: (student: Student) => (
      <Badge variant={getStatusBadgeVariant(student.status)}>
        {student.status}
      </Badge>
    ),
  },
  {
    key: "actions",
    header: "Actions",
    cell: (student: Student) => (
      <Link href={`/dashboard/students/${student.id}`}>
        <Button variant="ghost" size="sm">
          <Eye className="h-4 w-4 mr-1" />
          View
        </Button>
      </Link>
    ),
  },
];

export default function StudentsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

  const filteredStudents = demoStudents.filter((student) => {
    const matchesSearch =
      student.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      student.last_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      student.admission_number.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || student.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="flex flex-col">
      <Header
        title="Students"
        description="Manage student records and fee status"
      />

      <div className="flex-1 space-y-4 p-6">
        {/* Filters and Actions */}
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-1 gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search students..."
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
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="suspended">Suspended</SelectItem>
                <SelectItem value="graduated">Graduated</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add Student
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Add New Student</DialogTitle>
                <DialogDescription>
                  Enter the student details to register them in the system.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input id="firstName" placeholder="John" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input id="lastName" placeholder="Kamau" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="admissionNo">Admission Number</Label>
                    <Input id="admissionNo" placeholder="ADM-2024-001" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="grade">Grade/Class</Label>
                    <Input id="grade" placeholder="Form 3" />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="school">School</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select school" />
                    </SelectTrigger>
                    <SelectContent>
                      {demoSchools.map((school) => (
                        <SelectItem key={school.id} value={school.id.toString()}>
                          {school.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="guardianName">Guardian Name</Label>
                    <Input id="guardianName" placeholder="James Kamau" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="guardianPhone">Guardian Phone</Label>
                    <Input id="guardianPhone" placeholder="+254712345678" />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={() => setIsAddDialogOpen(false)}>
                  Add Student
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Summary Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-lg border bg-card p-4">
            <p className="text-sm text-muted-foreground">Total Students</p>
            <p className="text-2xl font-bold">{demoStudents.length}</p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-sm text-muted-foreground">Active</p>
            <p className="text-2xl font-bold text-success">
              {demoStudents.filter((s) => s.status === "active").length}
            </p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-sm text-muted-foreground">Total Outstanding</p>
            <p className="text-2xl font-bold text-destructive">
              {formatCurrency(demoStudents.reduce((sum, s) => sum + s.balance, 0))}
            </p>
          </div>
          <div className="rounded-lg border bg-card p-4">
            <p className="text-sm text-muted-foreground">Fully Paid</p>
            <p className="text-2xl font-bold text-success">
              {demoStudents.filter((s) => s.balance === 0).length}
            </p>
          </div>
        </div>

        {/* Data Table */}
        <DataTable
          columns={columns}
          data={filteredStudents}
          keyExtractor={(student) => student.id}
          emptyMessage="No students found"
        />
      </div>
    </div>
  );
}
