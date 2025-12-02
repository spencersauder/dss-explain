import type { ChangeEvent } from 'react';

interface FormFieldProps {
  label: string;
  name: string;
  type?: string;
  value: string | number;
  onChange: (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  min?: number;
  max?: number;
  step?: number;
  textarea?: boolean;
}

export function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  min,
  max,
  step,
  textarea = false,
}: FormFieldProps) {
  const commonProps = {
    name,
    value,
    onChange,
    min,
    max,
    step,
    className: 'form-input',
  } as const;

  return (
    <label className="form-field">
      <span className="form-label">{label}</span>
      {textarea ? <textarea rows={3} {...commonProps} /> : <input type={type} {...commonProps} />}
    </label>
  );
}
