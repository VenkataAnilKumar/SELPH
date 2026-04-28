"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-context";
import {
  InputField,
  SubmitButton,
  FormError,
  validateEmail,
  validatePassword,
} from "@/components/form-components";

export default function SignupPage() {
  const { signup, error, clearError } = useAuth();
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [validationErrors, setValidationErrors] = useState<{
    email?: string;
    password?: string;
    confirmPassword?: string;
  }>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearError();
    setValidationErrors({});
    setLoading(true);

    // Validation
    const newErrors: typeof validationErrors = {};

    if (!email) newErrors.email = "Email is required";
    else if (!validateEmail(email))
      newErrors.email = "Please enter a valid email";

    const passwordError = validatePassword(password);
    if (passwordError) newErrors.password = passwordError;

    if (!confirmPassword) newErrors.confirmPassword = "Please confirm your password";
    else if (password !== confirmPassword)
      newErrors.confirmPassword = "Passwords do not match";

    if (Object.keys(newErrors).length > 0) {
      setValidationErrors(newErrors);
      setLoading(false);
      return;
    }

    try {
      await signup(email, password);
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
            Create your account
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
            placeholder="Min 8 chars, uppercase, lowercase, number"
            value={password}
            onChange={setPassword}
            error={validationErrors.password}
            disabled={loading}
            required
          />

          <InputField
            id="confirmPassword"
            label="Confirm Password"
            type="password"
            placeholder="Re-enter your password"
            value={confirmPassword}
            onChange={setConfirmPassword}
            error={validationErrors.confirmPassword}
            disabled={loading}
            required
          />

          <SubmitButton
            label="Create Account"
            loading={loading}
            onClick={handleSubmit}
          />
        </form>

        {/* Footer */}
        <div className="text-center space-y-4">
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <Link href="/auth/login" className="text-blue-600 hover:text-blue-700 font-medium">
              Sign in
            </Link>
          </p>
          <p className="text-xs text-gray-500">
            By creating an account, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>

        {/* Password Requirements */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-xs font-semibold text-blue-900 mb-2">Password requirements:</p>
          <ul className="text-xs text-blue-800 space-y-1">
            <li>• At least 8 characters</li>
            <li>• At least one uppercase letter (A-Z)</li>
            <li>• At least one lowercase letter (a-z)</li>
            <li>• At least one number (0-9)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
