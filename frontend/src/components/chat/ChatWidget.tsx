'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import {
  Loader2,
  MessageCircle,
  Send,
  X,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  ExternalLink,
} from 'lucide-react';
import { useAuth } from '@/components/auth/AuthProvider';
import { sendChatMessage, type ChatTurn } from '@/lib/api';
import { useLanguageStore } from '@/stores/languageStore';
import { useSpeech } from '@/hooks/useSpeech';
import Logo from '@/components/ui/Logo';

export default function ChatWidget() {
  const { user } = useAuth();
  const t = useLanguageStore((s) => s.t);
  const language = useLanguageStore((s) => s.language);
  const welcome: ChatTurn = {
    role: 'assistant',
    content: t('chat.welcome'),
    confidence: 'high',
  };

  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatTurn[]>([welcome]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    isListening,
    isTranscribing,
    interimTranscript,
    sttError,
    isSTTSupported,
    toggleListening,
    stopListening,
    isSpeaking,
    speakingId,
    toggleSpeak,
    stopSpeaking,
  } = useSpeech();

  const listRef = useRef<HTMLDivElement>(null);
  const welcomeRef = useRef(welcome.content);

  useEffect(() => {
    setMessages(prev => {
      if (prev.length === 1 && prev[0].role === 'assistant') {
        welcomeRef.current = t('chat.welcome');
        return [{ role: 'assistant', content: t('chat.welcome'), confidence: 'high' }];
      }
      return prev;
    });
  }, [language, t]);

  useEffect(() => {
    if (!open) return;
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, open, loading, interimTranscript]);

  if (!user) return null;

  // Voice Input (Speech-to-Text)
  const handleMicClick = () => {
    toggleListening((text) => {
      setInput((prev) => (prev ? `${prev} ${text}` : text));
    });
  };

  async function handleSend(event?: React.FormEvent) {
    event?.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    if (isListening) {
      stopListening();
    }
    stopSpeaking();

    const nextHistory = [...messages, { role: 'user' as const, content: text }];
    setMessages(nextHistory);
    setInput('');
    setError(null);
    setLoading(true);

    try {
      const history = nextHistory
        .filter((m) => m.content !== welcomeRef.current)
        .slice(0, -1)
        .slice(-8);

      const langCode = (language === 'hi' || language === 'mr' ? language : 'en') as 'en' | 'hi' | 'mr';
      const res = await sendChatMessage(text, history, langCode);

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply,
          confidence: res.confidence || 'high',
          rag_status: res.rag_status,
          sources: res.sources,
        },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : t('chat.reachError');
      setError(message);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: t('chat.offline'), confidence: 'unverified' },
      ]);
    } finally {
      setLoading(false);
    }
  }

  // Render 3-tier Trust Badge
  const renderTrustBadge = (msg: ChatTurn) => {
    if (msg.role !== 'assistant') return null;

    const confidence = msg.confidence || 'unverified';
    const sources = msg.sources || [];

    if (confidence === 'high') {
      return (
        <div className="mt-2.5 pt-2 border-t border-border flex flex-wrap items-center gap-1.5 text-[11px] text-emerald-700 dark:text-emerald-400">
          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span className="font-semibold">{t('chat.verified')}</span>
          {sources.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              {sources.map((s, sIdx) => {
                const title = s.title || s.source_title || `Source ${sIdx + 1}`;
                const url = s.url || s.source_url;
                return url ? (
                  <a
                    key={sIdx}
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-0.5 underline font-medium hover:text-emerald-900 dark:hover:text-emerald-300 transition"
                  >
                    <span>{title}</span>
                    <ExternalLink className="h-2.5 w-2.5" />
                  </a>
                ) : (
                  <span key={sIdx} className="font-medium bg-emerald-50 dark:bg-emerald-950/40 px-1.5 py-0.5 rounded text-emerald-800 dark:text-emerald-300">
                    {title}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      );
    }

    if (confidence === 'medium') {
      return (
        <div className="mt-2.5 pt-2 border-t border-border flex items-center gap-1.5 text-[11px] text-amber-700 dark:text-amber-400">
          <AlertCircle className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
          <span className="font-semibold">{t('chat.partiallyVerified')}</span>
        </div>
      );
    }

    return (
      <div className="mt-2.5 pt-2 border-t border-border flex items-center justify-between gap-1 text-[11px] text-foreground-muted">
        <div className="flex items-center gap-1">
          <HelpCircle className="h-3.5 w-3.5 text-foreground-muted shrink-0" />
          <span>{t('chat.generalGuidance')}</span>
        </div>
        <Link href="/schemes" className="text-primary font-semibold hover:underline">
          {t('nav.schemes')} →
        </Link>
      </div>
    );
  };

  return (
    <div className="fixed bottom-24 right-4 sm:bottom-6 sm:right-6 z-[1100] flex flex-col items-end gap-3">
      {open && (
        <div className="flex h-[min(560px,80vh)] w-[min(420px,calc(100vw-2rem))] flex-col overflow-hidden rounded-[28px] border border-border bg-white dark:bg-[#161B22] shadow-2xl animate-in fade-in zoom-in-95 duration-200">
          {/* Header */}
          <div className="flex items-center justify-between bg-gradient-to-r from-primary to-[#0F7D57] px-5 py-4 text-white">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20 p-1 backdrop-blur-sm border border-white/30 shadow-sm">
                <Logo variant="icon" size={24} inverted />
              </div>
              <div>
                <p className="text-sm font-bold tracking-tight">{t('chat.title')}</p>
                <p className="text-[11px] text-white/80">{t('chat.subtitle')}</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => {
                stopListening();
                stopSpeaking();
                setOpen(false);
              }}
              className="rounded-full p-1.5 text-white/80 hover:bg-white/15 hover:text-white transition"
              aria-label={t('chat.close')}
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Chat message list */}
          <div ref={listRef} className="flex-1 space-y-3.5 overflow-y-auto bg-[#F9FAFB] dark:bg-[#0D1117] p-4">
            {messages.map((msg, idx) => {
              const msgId = `widget-msg-${idx}`;
              const isThisSpeaking = isSpeaking && speakingId === msgId;

              return (
                <div
                  key={`${msg.role}-${idx}`}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[90%] px-4 py-3 text-xs sm:text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'rounded-2xl rounded-br-sm bg-primary text-white font-medium shadow-pill-active'
                        : 'rounded-2xl rounded-bl-sm border border-border bg-white dark:bg-[#1C2128] text-foreground shadow-subtle'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 whitespace-pre-line">{msg.content}</div>
                      {msg.role === 'assistant' && (
                        <button
                          type="button"
                          onClick={() => toggleSpeak(msg.content, msgId)}
                          className={`p-1.5 rounded-lg transition shrink-0 ${
                            isThisSpeaking
                              ? 'text-primary bg-primary/10 animate-pulse'
                              : 'text-foreground-muted hover:text-foreground hover:bg-slate-100 dark:hover:bg-neutral-800'
                          }`}
                          title={isThisSpeaking ? t('chat.stopAudio') : t('chat.playAudio')}
                          aria-label="Text to speech"
                        >
                          {isThisSpeaking ? (
                            <VolumeX className="h-3.5 w-3.5" />
                          ) : (
                            <Volume2 className="h-3.5 w-3.5" />
                          )}
                        </button>
                      )}
                    </div>

                    {/* 3-tier Trust Badge */}
                    {renderTrustBadge(msg)}
                  </div>
                </div>
              );
            })}

            {/* Realtime STT listening or transcribing banner */}
            {isListening && (
              <div className="flex items-center gap-2.5 p-2.5 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-700 dark:text-emerald-300 text-xs animate-in fade-in">
                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-3 bg-emerald-500 animate-pulse rounded-full" />
                  <span className="w-1.5 h-4 bg-emerald-500 animate-pulse delay-75 rounded-full" />
                  <span className="w-1.5 h-2 bg-emerald-500 animate-pulse delay-150 rounded-full" />
                </div>
                <span className="font-semibold">{t('chat.listening')}</span>
                {interimTranscript && (
                  <span className="italic text-foreground-muted truncate">&ldquo;{interimTranscript}&rdquo;</span>
                )}
              </div>
            )}

            {isTranscribing && (
              <div className="flex items-center gap-2 p-2.5 bg-primary/10 border border-primary/20 rounded-xl text-primary text-xs animate-pulse">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                <span className="font-semibold">Transcribing with Sarvam AI...</span>
              </div>
            )}

            {loading && (
              <div className="flex items-center gap-2 text-xs font-semibold text-primary">
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                {t('chat.thinking')}
              </div>
            )}
          </div>

          {/* Chat input footer */}
          <form onSubmit={handleSend} className="border-t border-border bg-white dark:bg-[#161B22] p-3.5">
            {(error || sttError) && (
              <p className="mb-2 text-[11px] text-rose-600 dark:text-rose-400 font-semibold">
                {error || sttError}
              </p>
            )}
            <div className="flex items-end gap-2">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    void handleSend();
                  }
                }}
                rows={1}
                placeholder={
                  isListening
                    ? t('chat.listening')
                    : isTranscribing
                    ? 'Processing voice...'
                    : t('chat.placeholder')
                }
                className="max-h-24 min-h-[44px] flex-1 resize-none rounded-xl border border-border bg-[#F9FAFB] dark:bg-[#1C2128] px-3.5 py-3 text-xs sm:text-sm outline-none transition focus:border-primary focus:bg-white dark:focus:bg-[#161B22] focus:ring-2 focus:ring-primary/20 text-foreground placeholder:text-foreground-muted"
              />

              {/* Speech Recognition Button */}
              <button
                type="button"
                onClick={handleMicClick}
                disabled={!isSTTSupported || isTranscribing}
                className={`inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border transition ${
                  isListening
                    ? 'bg-rose-500 text-white border-rose-600 shadow-lg shadow-rose-500/30 animate-pulse'
                    : isTranscribing
                    ? 'bg-amber-500 text-white border-amber-600'
                    : 'bg-[#F9FAFB] dark:bg-[#1C2128] text-foreground-muted border-border hover:bg-slate-100 dark:hover:bg-neutral-800 hover:text-foreground'
                }`}
                title={isListening ? t('chat.stopMic') : t('chat.startMic')}
                aria-label="Voice input"
              >
                {isTranscribing ? (
                  <Loader2 className="h-4 w-4 animate-spin text-white" />
                ) : isListening ? (
                  <MicOff className="h-4 w-4" />
                ) : (
                  <Mic className="h-4 w-4" />
                )}
              </button>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-primary text-white shadow-pill-active transition hover:bg-primary-600 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-50"
                aria-label={t('chat.send')}
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </form>
        </div>
      )}

      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-primary text-white shadow-pill-active border border-white/20 transition-all duration-300 hover:bg-primary-600 hover:scale-105 active:scale-95"
        aria-label={open ? t('chat.close') : t('chat.open')}
      >
        {open ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>
    </div>
  );
}

