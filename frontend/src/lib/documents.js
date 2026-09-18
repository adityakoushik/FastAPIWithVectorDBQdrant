export const MAX_FILE_BYTES = 20 * 1024 * 1024;

export function validatePdf(file) {
  if (!file) return "Choose a PDF to continue.";
  if (!/\.pdf$/i.test(file.name))
    return "Only PDF files are supported. Please choose a .pdf file.";
  if (file.size === 0) return "This file is empty. Please choose another PDF.";
  if (file.size > MAX_FILE_BYTES)
    return "This PDF exceeds the 20 MB workspace limit. Please choose a smaller file.";
  return null;
}

export function formatBytes(bytes) {
  return bytes >= 1024 * 1024
    ? `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}
