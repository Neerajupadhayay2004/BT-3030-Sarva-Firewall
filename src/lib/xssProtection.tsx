/**
 * XSS Protection & Sanitization Utilities
 * Provides protection against Cross-Site Scripting attacks
 */

/**
 * Sanitize any string to prevent XSS attacks
 * Escapes all potentially dangerous HTML characters
 */
export const sanitizeHtml = (input: string): string => {
  if (typeof input !== 'string') {
    return String(input);
  }

  const div = document.createElement('div');
  div.textContent = input;
  return div.innerHTML;
};

/**
 * Sanitize URL search parameters
 * Prevents XSS via query parameters
 */
export const sanitizeSearchParams = (searchParams: URLSearchParams): Record<string, string> => {
  const sanitized: Record<string, string> = {};
  for (const [key, value] of searchParams) {
    sanitized[key] = sanitizeHtml(value);
  }
  return sanitized;
};

/**
 * Validate and sanitize URLs
 * Prevents javascript: URLs and other malicious schemes
 */
export const sanitizeUrl = (url: string): string => {
  try {
    const parsed = new URL(url, window.location.origin);
    
    // Only allow safe protocols
    const safeProtocols = ['http:', 'https:'];
    if (!safeProtocols.includes(parsed.protocol)) {
      return '#';
    }
    
    // Sanitize all query parameters
    const sanitizedParams = new URLSearchParams();
    for (const [key, value] of parsed.searchParams) {
      sanitizedParams.set(key, sanitizeHtml(value));
    }
    parsed.search = sanitizedParams.toString();
    
    return parsed.toString();
  } catch {
    return '#';
  }
};

/**
 * Safe component for rendering potentially unsafe content
 * Automatically sanitizes any string before rendering
 */
import React from 'react';

interface SafeTextProps {
  children: string;
  className?: string;
  tag?: keyof JSX.IntrinsicElements;
}

export const SafeText: React.FC<SafeTextProps> = ({ 
  children, 
  className, 
  tag: Tag = 'span' 
}) => {
  const sanitized = sanitizeHtml(children);
  return <Tag className={className}>{sanitized}</Tag>;
};

/**
 * Safe component for rendering preformatted text
 * Used in simulator results to prevent XSS
 */
export const SafePre: React.FC<{ children: string; className?: string }> = ({ 
  children, 
  className 
}) => {
  const sanitized = sanitizeHtml(children);
  return <pre className={className}>{sanitized}</pre>;
};

/**
 * XSS Detection - Check if string contains potentially malicious patterns
 */
export const detectXss = (input: string): boolean => {
  const xssPatterns = [
    /<script\b[^>]*>([\s\S]*?)<\/script>/gi,
    /<iframe\b[^>]*>([\s\S]*?)<\/iframe>/gi,
    /javascript:/gi,
    /on\w+=(?:['"]|)(?:[^\s>])+?(?:['"]|)/gi,
    /<img\b[^>]*src=/gi,
    /<svg\b[^>]*onload=/gi,
    /eval\s*\(/gi,
    /document\.cookie/gi,
    /document\.location/gi,
    /window\./gi,
    /<\s*script/gi,
    /<\s*iframe/gi
  ];

  return xssPatterns.some(pattern => pattern.test(input));
};

/**
 * Sanitize form input before sending to backend
 */
export const sanitizeFormInput = (input: any): any => {
  if (typeof input === 'string') {
    return sanitizeHtml(input);
  }
  if (typeof input === 'object' && input !== null) {
    if (Array.isArray(input)) {
      return input.map(sanitizeFormInput);
    }
    const sanitized: any = {};
    for (const [key, value] of Object.entries(input)) {
      sanitized[key] = sanitizeFormInput(value);
    }
    return sanitized;
  }
  return input;
};