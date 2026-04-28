"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  InputField,
  SubmitButton,
  FormError,
  validateEmail,
} from "@/components/form-components";

export default function LoginPage() {
  const { login, error, clearError } = useAuth();
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [validationErrors, setValidationErrors] = useState<{
    email?: string;
    password?: string;
  }>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationErrors({});
    setLoading(true);

    // Validation
    const newErrors: typeof validationErrors = {};
    if (!email) newErrors.email = "Email is required";
    else if (!validateEmail(email)) newErrors.email = "Please enter a valid email";
    if (!password) newErrors.password = "Password is required";

    if (Object.keys(newErrors).length > 0) {
      setValidationErrors(newErrors);
      setLoading(false);
      return;
    }

    try {
      await login(email, password);
    } catch (err) {
      // Error is handled by auth context
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">SELPH</h1>
          <p className="mt-2 text-gray-600">Your Digital Twin AI</p>
          <h2 className="mt-6 text-2xl font-bold text-gray-900">
            Sign in to your account
          </h2>
        </div>

        {/* Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && <FormError message={error} />}

          <InputField
            id="email"
            label="Email Address"
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={setEmail}
            error={validationErrors.email}
            disabled={loading}
            required
          />

          <InputField
            id="password"
            label="Password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={setPassword}
            error={validationErrors.password}
            disabled={loading}
            required
          />

          <SubmitButton
            label="Sign in"
            loading={loading}
            onClick={handleSubmit}
          />
        </form>

        {/* Footer */}
        <div className="text-center space-y-4">
          <p className="text-sm text-gray-600">
            Don't have an account?{" "}
            <Link href="/auth/signup" className="text-blue-600 hover:text-blue-700 font-medium">
              Sign up
            </Link>
          </p>
          <p className="text-xs text-gray-500">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
}
