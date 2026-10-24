import React, { useState } from 'react';
import { Header } from './components/Header';
import { ReferenceAudioCard } from './components/ReferenceAudioCard';
import { ConsentCard } from './components/ConsentCard';
import { TextInputCard } from './components/TextInputCard';
import { OutputPlayerCard } from './components/OutputPlayerCard';
import { CliGuideModal } from './components/CliGuideModal';
import { AudioMetadata, GenerationResponse, LanguageOption } from './types';

const LANGUAGES: LanguageOption[] = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'it', name: 'Italian' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'pl', name: 'Polish' },
  { code: 'tr', name: 'Turkish' },
  { code: 'ru', name: 'Russian' },
  { code: 'nl', name: 'Dutch' },
  { code: 'cs', name: 'Czech' },
  { code: 'ar', name: 'Arabic' },
  { code: 'zh', name: 'Chinese' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'hi', name: 'Hindi' },
];

export default function App() {
  const [refAudioBase64, setRefAudioBase64] = useState<string | null>(null);
  const [refMetadata, setRefMetadata] = useState<AudioMetadata | null>(null);
  const [audioValidationLoading, setAudioValidationLoading] = useState(false);
  const [audioError, setAudioError] = useState<string | null>(null);

  const [hasPermission, setHasPermission] = useState<boolean>(false);

  const [text, setText] = useState<string>(
    'Welcome to the AI-Based Voice Cloning System. This speech is generated using reference-conditioned acoustic modeling.'
  );
  const [selectedLang, setSelectedLang] = useState<string>('en');

  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);
  const [generatedResult, setGeneratedResult] = useState<GenerationResponse | null>(null);

  const [activeTab, setActiveTab] = useState<'app' | 'cli'>('app');

  const handleLoadSample = async () => {
    try {
      setAudioValidationLoading(true);
      setAudioError(null);
      const res = await fetch('/api/sample-audio');
      if (!res.ok) throw new Error('Failed to fetch bundled sample audio');
      const data = await res.json();
      setRefAudioBase64(data.base64);

      setRefMetadata({
        filename: data.filename,
        duration: data.duration,
        sampleRate: data.sampleRate,
        channels: data.channels,
        format: data.format,
        fileSizeBytes: data.sizeBytes,
        is_valid: true,
        peaks: Array.from({ length: 40 }, () => 0.2 + Math.random() * 0.6),
      });
    } catch (err: any) {
      setAudioError(err.message || 'Error loading sample voice');
    } finally {
      setAudioValidationLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setAudioValidationLoading(true);
    setAudioError(null);
    setRefMetadata(null);

    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const base64Data = (reader.result as string).split(',')[1];
        setRefAudioBase64(base64Data);

        const res = await fetch('/api/validate-audio', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            base64Audio: base64Data,
            filename: file.name,
          }),
        });

        const data = await res.json();
        if (!data.is_valid) {
          setAudioError(data.error_message || 'Audio validation failed');
          setRefMetadata(null);
        } else {
          setRefMetadata({
            filename: data.filename,
            duration: data.duration,
            sampleRate: data.sampleRate,
            channels: data.channels,
            format: data.format,
            fileSizeBytes: data.fileSizeBytes,
            peaks: data.peaks || [],
            is_valid: true,
          });
        }
      } catch (err: any) {
        setAudioError(err.message || 'Error analyzing audio recording');
      } finally {
        setAudioValidationLoading(false);
      }
    };
    reader.readAsDataURL(file);
  };

  const handleGenerate = async () => {
    if (!hasPermission) {
      setGenerationError('Authorization confirmation is required before speech generation.');
      return;
    }
    if (!refAudioBase64 || !refMetadata?.is_valid) {
      setGenerationError('Please upload and validate a reference audio recording first.');
      return;
    }
    if (!text.trim()) {
      setGenerationError('The entered text cannot be empty or whitespace.');
      return;
    }
    if (text.length > 1000) {
      setGenerationError('Text exceeds the maximum allowed length of 1,000 characters.');
      return;
    }

    setIsGenerating(true);
    setGenerationError(null);

    try {
      const res = await fetch('/api/clone-voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text.trim(),
          base64Audio: refAudioBase64,
          filename: refMetadata.filename,
          language: selectedLang,
          hasPermission: true,
        }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error_message || 'Failed to synthesize speech');
      }

      setGeneratedResult(data);
    } catch (err: any) {
      setGenerationError(err.message || 'An error occurred during speech generation');
    } finally {
      setIsGenerating(false);
    }
  };

  const canGenerate = Boolean(
    refAudioBase64 && refMetadata?.is_valid && hasPermission && text.trim().length > 0 && text.length <= 1000 && !isGenerating
  );

  const getDisabledReason = () => {
    if (!refMetadata?.is_valid) return 'Upload or load a reference audio recording to begin';
    if (!hasPermission) return 'Confirm speaker authorization above to unlock generation';
    if (!text.trim()) return 'Enter text to synthesize';
    return '';
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
      <Header activeTab={activeTab} onToggleTab={() => setActiveTab(activeTab === 'app' ? 'cli' : 'app')} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeTab === 'cli' ? (
          <CliGuideModal onClose={() => setActiveTab('app')} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            <div className="lg:col-span-5 space-y-6">
              <ReferenceAudioCard
                metadata={refMetadata}
                audioBase64={refAudioBase64}
                loading={audioValidationLoading}
                error={audioError}
                onLoadSample={handleLoadSample}
                onFileUpload={handleFileUpload}
              />

              <ConsentCard hasPermission={hasPermission} onConsentChange={setHasPermission} />
            </div>

            <div className="lg:col-span-7 space-y-6">
              <TextInputCard
                text={text}
                onTextChange={setText}
                selectedLang={selectedLang}
                onLangChange={setSelectedLang}
                languages={LANGUAGES}
                onGenerate={handleGenerate}
                canGenerate={canGenerate}
                isGenerating={isGenerating}
                generationError={generationError}
                disabledReason={getDisabledReason()}
              />

              {generatedResult && <OutputPlayerCard result={generatedResult} />}
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-4 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>AI-Based Voice Cloning System • Decoupled Frontend &amp; Backend Architecture</span>
          <span className="text-slate-400">
            Compliant with Educational &amp; Authorized Vocal Consent Standards
          </span>
        </div>
      </footer>
    </div>
  );
}
