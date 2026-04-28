/**
 * Reusable form components for authentication
 */

import React from "react";

interface InputFieldProps {
  id: string;
  label: string;
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
}

export const InputField = ({
  id,
  label,
  type = "text",
  placeholder,
  value,
  onChange,
  error,
  disabled,
  required,
}: InputFieldProps) => {
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-gray-700">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <input
        id={id}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={`mt-2 w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error
            ? "border-red-500 focus:ring-red-500"
            : "border-gray-300"
        } ${disabled ? "bg-gray-100 cursor-not-allowed" : ""}`}
      />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
};

interface SubmitButtonProps {
  label: string;
  loading?: boolean;
  disabled?: boolean;
  onClick?: (e: React.FormEvent) => void;
}

export const SubmitButton = ({
  label,
  loading,
  disabled,
  onClick,
}: SubmitButtonProps) => {
  return (
    <button
      type="submit"
      onClick={onClick}
      disabled={loading || disabled}
      className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${
        loading || disabled
          ? "bg-gray-400 cursor-not-allowed"
          : "bg-blue-600 hover:bg-blue-700"
      }`}
    >
      {loading ? "Loading..." : label}
    </button>
  );
};

interface FormErrorProps {
  message: string;
}

export const FormError = ({ message }: FormErrorProps) => {
  return (
    <div className="p-4 mb-4 bg-red-50 border border-red-200 rounded-lg">
      <p className="text-sm text-red-700">{message}</p>
    </div>
  );
};

interface FormSuccessProps {
  message: string;
}

export const FormSuccess = ({ message }: FormSuccessProps) => {
  return (
    <div className="p-4 mb-4 bg-green-50 border border-green-200 rounded-lg">
      <p className="text-sm text-green-700">{message}</p>
    </div>
  );
};

/**
 * Validate email format
 */
export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Validate password strength
 */
export const validatePassword = (password: string): string | null => {
  if (!password) return "Password is required";
  if (password.length < 8)
    return "Password must be at least 8 characters long";
  if (!/[A-Z]/.test(password))
    return "Password must contain at least one uppercase letter";
  if (!/[a-z]/.test(password))
    return "Password must contain at least one lowercase letter";
  if (!/[0-9]/.test(password))
    return "Password must contain at least one number";
  return null;
};
