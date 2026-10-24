export interface AudioMetadata {
  filename: string;
  duration: number;
  sampleRate: number;
  channels: number;
  format: string;
  fileSizeBytes: number;
  peaks?: number[];
  is_valid: boolean;
  error_message?: string;
}

export interface GenerationResponse {
  success: boolean;
  filename: string;
  duration: number;
  latency: number;
  sampleRate: number;
  format: string;
  base64Audio: string;
  mimeType: string;
  error_message?: string;
  disclaimer: string;
}

export interface LanguageOption {
  code: string;
  name: string;
}
