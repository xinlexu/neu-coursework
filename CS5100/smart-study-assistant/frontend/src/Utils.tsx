import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Utility function to conditionally merge class names.
 * @param inputs ClassValue[] - Variable number of class name inputs.
 * @returns string - Merged class names.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}