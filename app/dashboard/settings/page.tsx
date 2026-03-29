"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { 
  Shield, 
  Key, 
  Bell, 
  Smartphone, 
  CheckCircle, 
  XCircle,
  Loader2,
  AlertCircle,
  Eye,
  EyeOff,
  ExternalLink,
} from "lucide-react";
import { settingsApi, type MpesaSettingsResponse, type TestConnectionResponse } from "@/lib/api";

export default function SettingsPage() {
  // M-Pesa credentials state
  const [consumerKey, setConsumerKey] = useState("");
  const [consumerSecret, setConsumerSecret] = useState("");
  const [environment, setEnvironment] = useState("sandbox");
  const [callbackUrl, setCallbackUrl] = useState("");
  
  // UI state
  const [showKey, setShowKey] = useState(false);
  const [showSecret, setShowSecret] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [currentConfig, setCurrentConfig] = useState<MpesaSettingsResponse | null>(null);
  const [testResult, setTestResult] = useState<TestConnectionResponse | null>(null);
  const [saveMessage, setSaveMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Load current settings on mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const config = await settingsApi.getMpesaSettings();
      setCurrentConfig(config);
      setEnvironment(config.environment);
      setCallbackUrl(config.callback_url || "");
    } catch (error) {
      console.error("Failed to load settings:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!consumerKey || !consumerSecret) {
      setSaveMessage({ type: "error", text: "Please enter both Consumer Key and Consumer Secret" });
      return;
    }

    setIsSaving(true);
    setSaveMessage(null);
    setTestResult(null);

    try {
      const response = await settingsApi.saveMpesaSettings({
        consumer_key: consumerKey,
        consumer_secret: consumerSecret,
        environment,
        callback_url: callbackUrl || undefined,
      });

      setCurrentConfig(response);
      setConsumerKey("");
      setConsumerSecret("");
      setSaveMessage({ type: "success", text: "Credentials saved successfully!" });
    } catch (error) {
      setSaveMessage({ 
        type: "error", 
        text: error instanceof Error ? error.message : "Failed to save credentials" 
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);

    try {
      const result = await settingsApi.testConnection();
      setTestResult(result);
    } catch (error) {
      setTestResult({
        success: false,
        message: error instanceof Error ? error.message : "Connection test failed",
        access_token_obtained: false,
        environment: environment,
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleClearCredentials = async () => {
    if (!confirm("Are you sure you want to clear your M-Pesa credentials?")) {
      return;
    }

    try {
      await settingsApi.clearMpesaSettings();
      setCurrentConfig(null);
      setTestResult(null);
      setSaveMessage({ type: "success", text: "Credentials cleared" });
      await loadSettings();
    } catch (error) {
      setSaveMessage({ 
        type: "error", 
        text: error instanceof Error ? error.message : "Failed to clear credentials" 
      });
    }
  };

  return (
    <div className="flex flex-col">
      <Header
        title="Settings"
        description="Configure M-Pesa integration for payments"
      />

      <div className="flex-1 p-6">
        <Tabs defaultValue="mpesa" className="space-y-6">
          <TabsList>
            <TabsTrigger value="mpesa">M-Pesa Integration</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
          </TabsList>

          <TabsContent value="mpesa" className="space-y-6">
            {/* Status Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Smartphone className="h-5 w-5" />
                      M-Pesa Daraja API Status
                    </CardTitle>
                    <CardDescription>
                      Current configuration status for M-Pesa payments
                    </CardDescription>
                  </div>
                  {isLoading ? (
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Loading
                    </Badge>
                  ) : currentConfig?.is_configured ? (
                    <Badge className="flex items-center gap-1 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30">
                      <CheckCircle className="h-3 w-3" />
                      Configured
                    </Badge>
                  ) : (
                    <Badge variant="destructive" className="flex items-center gap-1">
                      <XCircle className="h-3 w-3" />
                      Not Configured
                    </Badge>
                  )}
                </div>
              </CardHeader>
              {currentConfig && (
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-lg border bg-card p-3">
                      <p className="text-xs text-muted-foreground">Consumer Key</p>
                      <p className="font-medium">
                        {currentConfig.consumer_key_set ? (
                          <span className="flex items-center gap-1 text-emerald-400">
                            <CheckCircle className="h-3 w-3" /> Set
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-destructive">
                            <XCircle className="h-3 w-3" /> Not Set
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="rounded-lg border bg-card p-3">
                      <p className="text-xs text-muted-foreground">Consumer Secret</p>
                      <p className="font-medium">
                        {currentConfig.consumer_secret_set ? (
                          <span className="flex items-center gap-1 text-emerald-400">
                            <CheckCircle className="h-3 w-3" /> Set
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-destructive">
                            <XCircle className="h-3 w-3" /> Not Set
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="rounded-lg border bg-card p-3">
                      <p className="text-xs text-muted-foreground">Environment</p>
                      <p className="font-medium capitalize">{currentConfig.environment}</p>
                    </div>
                    <div className="rounded-lg border bg-card p-3">
                      <p className="text-xs text-muted-foreground">Shortcode</p>
                      <p className="font-medium font-mono">{currentConfig.shortcode}</p>
                    </div>
                  </div>
                  {currentConfig.last_updated && (
                    <p className="mt-4 text-xs text-muted-foreground">
                      Last updated: {new Date(currentConfig.last_updated).toLocaleString()}
                    </p>
                  )}
                </CardContent>
              )}
            </Card>

            {/* Credentials Form */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Key className="h-5 w-5" />
                  {currentConfig?.is_configured ? "Update Credentials" : "Add M-Pesa Credentials"}
                </CardTitle>
                <CardDescription>
                  Enter your Safaricom Daraja API credentials. Get them from{" "}
                  <a 
                    href="https://developer.safaricom.co.ke" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-primary hover:underline inline-flex items-center gap-1"
                  >
                    developer.safaricom.co.ke
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="consumerKey">Consumer Key *</Label>
                    <div className="relative">
                      <Input 
                        id="consumerKey" 
                        type={showKey ? "text" : "password"}
                        placeholder="Enter your Consumer Key"
                        value={consumerKey}
                        onChange={(e) => setConsumerKey(e.target.value)}
                        className="pr-10"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                        onClick={() => setShowKey(!showKey)}
                      >
                        {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="consumerSecret">Consumer Secret *</Label>
                    <div className="relative">
                      <Input 
                        id="consumerSecret" 
                        type={showSecret ? "text" : "password"}
                        placeholder="Enter your Consumer Secret"
                        value={consumerSecret}
                        onChange={(e) => setConsumerSecret(e.target.value)}
                        className="pr-10"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                        onClick={() => setShowSecret(!showSecret)}
                      >
                        {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Environment</Label>
                    <Select value={environment} onValueChange={setEnvironment}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sandbox">Sandbox (Testing)</SelectItem>
                        <SelectItem value="production">Production (Live)</SelectItem>
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-muted-foreground">
                      Use Sandbox for testing, Production for live payments
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="callbackUrl">Callback URL (Optional)</Label>
                    <Input 
                      id="callbackUrl" 
                      type="url"
                      placeholder="https://your-domain.com/api/v1/payments/callback"
                      value={callbackUrl}
                      onChange={(e) => setCallbackUrl(e.target.value)}
                    />
                    <p className="text-xs text-muted-foreground">
                      For localhost testing, use ngrok to create a public URL
                    </p>
                  </div>
                </div>

                {/* Messages */}
                {saveMessage && (
                  <div className={`flex items-center gap-2 rounded-lg p-3 ${
                    saveMessage.type === "success" 
                      ? "bg-emerald-500/10 text-emerald-400" 
                      : "bg-destructive/10 text-destructive"
                  }`}>
                    {saveMessage.type === "success" ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <AlertCircle className="h-4 w-4" />
                    )}
                    {saveMessage.text}
                  </div>
                )}

                <div className="flex justify-between">
                  <div>
                    {currentConfig?.is_configured && (
                      <Button 
                        variant="outline" 
                        onClick={handleClearCredentials}
                        className="text-destructive hover:text-destructive"
                      >
                        Clear Credentials
                      </Button>
                    )}
                  </div>
                  <Button onClick={handleSave} disabled={isSaving || !consumerKey || !consumerSecret}>
                    {isSaving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      "Save Credentials"
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Test Connection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Test Connection
                </CardTitle>
                <CardDescription>
                  Verify your credentials by testing the connection to Safaricom API
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {testResult && (
                  <div className={`flex items-start gap-3 rounded-lg p-4 ${
                    testResult.success 
                      ? "bg-emerald-500/10 border border-emerald-500/20" 
                      : "bg-destructive/10 border border-destructive/20"
                  }`}>
                    {testResult.success ? (
                      <CheckCircle className="h-5 w-5 text-emerald-400 mt-0.5" />
                    ) : (
                      <XCircle className="h-5 w-5 text-destructive mt-0.5" />
                    )}
                    <div>
                      <p className={`font-medium ${testResult.success ? "text-emerald-400" : "text-destructive"}`}>
                        {testResult.success ? "Connection Successful" : "Connection Failed"}
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">{testResult.message}</p>
                      {testResult.access_token_obtained && (
                        <p className="text-xs text-muted-foreground mt-2">
                          Access token obtained from {testResult.environment} environment
                        </p>
                      )}
                    </div>
                  </div>
                )}

                <Button 
                  onClick={handleTestConnection} 
                  disabled={isTesting || !currentConfig?.is_configured}
                  variant="outline"
                >
                  {isTesting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Testing...
                    </>
                  ) : (
                    "Test Connection"
                  )}
                </Button>

                {!currentConfig?.is_configured && (
                  <p className="text-sm text-muted-foreground">
                    Save your credentials first before testing the connection.
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Help Card */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Setup Guide</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
                  <li>
                    Go to{" "}
                    <a 
                      href="https://developer.safaricom.co.ke" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      developer.safaricom.co.ke
                    </a>
                    {" "}and create an account
                  </li>
                  <li>Create a new app and select <strong>Lipa Na M-Pesa Sandbox</strong></li>
                  <li>Copy your <strong>Consumer Key</strong> and <strong>Consumer Secret</strong></li>
                  <li>Paste them above and click <strong>Save Credentials</strong></li>
                  <li>Click <strong>Test Connection</strong> to verify everything works</li>
                  <li>Go to <strong>Payments</strong> page to initiate STK Push requests</li>
                </ol>
                <div className="rounded-lg bg-muted/50 p-3 text-sm">
                  <p className="font-medium">Note on Callbacks:</p>
                  <p className="text-muted-foreground mt-1">
                    For localhost testing, M-Pesa needs a public callback URL. Use{" "}
                    <a 
                      href="https://ngrok.com" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      ngrok
                    </a>
                    {" "}to expose your local server: <code className="bg-background px-1 py-0.5 rounded">ngrok http 8000</code>
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  SMS Notifications
                </CardTitle>
                <CardDescription>
                  Configure automated SMS reminders and alerts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Payment Confirmation</p>
                      <p className="text-sm text-muted-foreground">Send SMS when payment is received</p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Payment Reminders</p>
                      <p className="text-sm text-muted-foreground">Send reminders before due date</p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Overdue Alerts</p>
                      <p className="text-sm text-muted-foreground">Send alerts for overdue payments</p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">Enabled</Badge>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Reminder Days Before Due</Label>
                  <Select defaultValue="3">
                    <SelectTrigger className="w-[200px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1 day</SelectItem>
                      <SelectItem value="3">3 days</SelectItem>
                      <SelectItem value="7">7 days</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="security" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Security Settings
                </CardTitle>
                <CardDescription>
                  Security features are automatically enabled
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Rate Limiting</p>
                      <p className="text-sm text-muted-foreground">100 requests per minute per IP</p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Input Sanitization</p>
                      <p className="text-sm text-muted-foreground">All inputs are validated and sanitized</p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Credential Encryption</p>
                      <p className="text-sm text-muted-foreground">API credentials stored securely</p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Audit Logging</p>
                      <p className="text-sm text-muted-foreground">All API requests are logged</p>
                    </div>
                    <Badge className="bg-emerald-500/20 text-emerald-400">Active</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
