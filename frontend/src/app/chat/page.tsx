'use client';

import React, { useState, useEffect, useRef } from 'react';
import AppShell from '@/components/ui/AppShell';
import { useLanguageStore, useTranslation } from '@/stores/languageStore';
import { useSpeech } from '@/hooks/useSpeech';
import { sendChatMessage, ChatTurn } from '@/lib/api';
import {
  Bot,
  Mic,
  MicOff,
  Send,
  Sparkles,
  Volume2,
  VolumeX,
  ShieldCheck,
  ExternalLink,
  Loader2,
  HelpCircle,
  RefreshCw,
  Lightbulb,
} from 'lucide-react';
import Card from '@/components/ui/Card';

const SAMPLE_QUESTIONS: Record<string, string[]> = {
  en: [
    'How do I apply for the PMEGP 35% subsidy & PM MUDRA loan?',
    'What is the working capital and setup cost for an oil mill / agro-processing unit?',
    'Which central & state government schemes support dairy, farming & micro-enterprises?',
    'How can I check APMC mandi prices and improve my credit readiness for bank loans?',
  ],
  hi: [
    'पीएमईजीपी ३५% सब्सिडी और मुद्रा लोन के लिए आवेदन कैसे करें?',
    'तेल मिल या कृषि प्रसंस्करण इकाई के लिए कितनी कार्यशील पूंजी चाहिए?',
    'भारत भर में डेयरी, कृषि और सूक्ष्म उद्यमों के लिए कौन सी केंद्रीय व राज्य योजनाएँ हैं?',
    'अपने जिले में मंडी भाव और बैंक लोन के लिए क्रेडिट स्कोर कैसे सुधारें?',
  ],
  mr: [
    'पीएमईजीपी ३५% अनुदान आणि मुद्रा कर्जासाठी अर्ज कसा करावा?',
    'तेल मिल किंवा कृषी प्रक्रिया उद्योगासाठी किती खेळते भांडवल आवश्यक आहे?',
    'विविध राज्यांमध्ये दुग्धव्यवसाय, शेती व सूक्ष्म उद्योगांसाठी कोणत्या योजना आहेत?',
    'आपल्या जिल्ह्यातील बाजारभाव आणि बँक कर्जासाठी क्रेडिट पात्रता कशी सुधारावी?',
  ],
  ta: [
    'PMEGP 35% மானியம் மற்றும் முத்ரா கடனுக்கு எவ்வாறு விண்ணப்பிப்பது?',
    'எண்ணெய் ஆலை அமைப்பதற்கான நடைமுறை மூலதனம் மற்றும் செலவு என்ன?',
    'விவசாயம் மற்றும் குறுந்தொழில்களுக்கு என்ன அரசு திட்டங்கள் உள்ளன?',
  ],
  te: [
    'PMEGP 35% సబ్సిడీ మరియు ముద్రా లోన్ కోసం ఎలా దరఖాస్తు చేయాలి?',
    'ఆయిల్ మిల్లు స్థాపనకు ఎంత వర్కింగ్ క్యాపిటల్ అవసరం?',
    'వ్యవసాయం మరియు సూక్ష్మ పరిశ్రమలకు ఏ ప్రభుత్వ పథకాలు అందుబాటులో ఉన్నాయి?',
  ],
  kn: [
    'PMEGP 35% ಸಬ್ಸಿಡಿ ಮತ್ತು ಮುದ್ರಾ ಸಾಲಕ್ಕೆ ಅರ್ಜಿ ಸಲ್ಲಿಸುವುದು ಹೇಗೆ?',
    'ಎಣ್ಣೆ ಗಿರಣಿ ಸ್ಥಾಪನೆಗೆ ಎಷ್ಟು ಬಂಡವಾಳ ಬೇಕು?',
    'ಕೃಷಿ ಮತ್ತು ಸಣ್ಣ ಉದ್ಯಮಗಳಿಗೆ ಯಾವ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳು ಲಭ್ಯವಿವೆ?',
  ],
  gu: [
    'PMEGP 35% સબસિડી અને મુદ્રા લોન માટે કેવી રીતે અરજી કરવી?',
    'તેલ મિલ શરૂ કરવા માટે કેટલી મૂડીની જરૂર પડશે?',
    'કૃષિ અને લઘુ ઉદ્યોગો માટે કઈ સરકારી યોજનાઓ ઉપલબ્ધ છે?',
  ],
  bn: [
    'PMEGP ৩৫% ভর্তুকি এবং মুদ্রা ঋণের জন্য কীভাবে আবেদন করবেন?',
    'তেল কল স্থাপনের জন্য কত চলতি মূলধন প্রয়োজন?',
    'কৃষি এবং ক্ষুদ্র শিল্পের জন্য কোন সরকারি প্রকল্প উপলব্ধ আছে?',
  ],
  pa: [
    'PMEGP 35% ਸਬਸਿਡੀ ਅਤੇ ਮੁਦਰਾ ਲੋਨ ਲਈ ਅਰਜ਼ੀ ਕਿਵੇਂ ਦੇਣੀ ਹੈ?',
    'ਤੇਲ ਮਿੱਲ ਸਥਾਪਤ ਕਰਨ ਲਈ ਕਿੰਨੀ ਕਾਰਜਸ਼ੀਲ ਪੂੰਜੀ ਦੀ ਲੋੜ ਹੈ?',
  ],
  ml: [
    'PMEGP 35% സബ്‌സിഡിക്കും മുദ്ര വായ്പയ്ക്കും എങ്ങനെ അപേക്ഷിക്കാം?',
    'ഒരു എണ്ണ മിൽ ആരംഭിക്കുന്നതിനുള്ള ചെലവ് എത്രയാണ്?',
  ],
};

export default function ChatPage() {
  const { language, t } = useLanguageStore();
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    isListening,
    isTranscribing,
    interimTranscript,
    sttError,
    isSTTSupported,
    startListening,
    stopListening,
    toggleListening,
    isSpeaking,
    speakingId,
    toggleSpeak,
    stopSpeaking,
  } = useSpeech();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize welcome message matching active language
  useEffect(() => {
    const welcome = t('chat.welcome');
    setMessages([
      {
        role: 'assistant',
        content: welcome,
        confidence: 'high',
      },
    ]);
  }, [language, t]);

  // Auto-scroll on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, interimTranscript, loading]);

  async function handleSend(textToSend?: string) {
    const text = (textToSend || input).trim();
    if (!text || loading) return;

    if (isListening) {
      stopListening();
    }
    stopSpeaking();

    const nextHistory: ChatTurn[] = [...messages, { role: 'user', content: text }];
    setMessages(nextHistory);
    setInput('');
    setError(null);
    setLoading(true);

    try {
      const historyToSend = nextHistory
        .filter((_, idx) => idx > 0) // skip initial greeting
        .slice(-6);

      const langCode = (language === 'hi' || language === 'mr' ? language : 'en') as 'en' | 'hi' | 'mr';
      const res = await sendChatMessage(text, historyToSend, langCode);

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
    } catch (err: any) {
      setError(err?.message || t('chat.reachError'));
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: t('chat.offline'),
          confidence: 'unverified',
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const handleMicClick = () => {
    toggleListening((finalText) => {
      setInput((prev) => (prev ? `${prev} ${finalText}` : finalText));
    });
  };

  const sampleList = SAMPLE_QUESTIONS[language] || SAMPLE_QUESTIONS.en;

  return (
    <AppShell>
      <main className="flex-1 max-w-5xl mx-auto p-3 sm:p-6 lg:p-8 w-full flex flex-col h-[calc(100vh-4rem)]">
        {/* Header Banner */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-primary via-emerald-700 to-slate-900 p-5 text-white shadow-fintech-card mb-4 shrink-0">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-white/20 backdrop-blur-md text-white rounded-full text-xs font-semibold">
                  <Bot className="h-3.5 w-3.5" /> UdyamAI Voice Advisor
                </span>
                <span className="text-xs bg-emerald-500/30 text-emerald-200 border border-emerald-400/30 px-2 py-0.5 rounded-full font-medium">
                  {language === 'mr' ? 'मराठी' : language === 'hi' ? 'हिंदी' : 'English'}
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-black tracking-tight">{t('module.chatTitle')}</h1>
            </div>

            <div className="flex items-center gap-2 text-xs">
              {isSTTSupported ? (
                <div className="flex items-center gap-1.5 bg-black/20 border border-white/10 px-3 py-1.5 rounded-full text-emerald-300">
                  <Mic className="h-3.5 w-3.5" />
                  <span>Voice Enabled (STT + TTS)</span>
                </div>
              ) : (
                <div className="text-amber-200 bg-amber-900/30 px-3 py-1.5 rounded-full border border-amber-500/30">
                  Voice requires Chrome/Safari
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Chat Messages Window */}
        <div className="flex-1 overflow-y-auto space-y-4 p-4 rounded-2xl border border-border bg-slate-50/50 dark:bg-[#12161F] shadow-inner mb-4">
          {messages.map((msg, idx) => {
            const isUser = msg.role === 'user';
            const msgId = `msg-${idx}`;
            const isThisSpeaking = isSpeaking && speakingId === msgId;

            return (
              <div key={idx} className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} gap-1.5`}>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground px-1">
                  {isUser ? (
                    <span className="font-semibold">You</span>
                  ) : (
                    <div className="flex items-center gap-1 text-primary font-semibold">
                      <Sparkles className="h-3 w-3" />
                      <span>UdyamAI Advisor</span>
                    </div>
                  )}
                </div>

                <div
                  className={`max-w-[88%] sm:max-w-[78%] rounded-2xl p-4 text-sm leading-relaxed shadow-subtle transition-all ${
                    isUser
                      ? 'bg-primary text-white rounded-tr-none font-medium'
                      : 'bg-white dark:bg-[#161B22] border border-border text-foreground rounded-tl-none'
                  }`}
                >
                  <p className="whitespace-pre-line">{msg.content}</p>

                  {/* Verification Badge & Speech Controls for AI Responses */}
                  {!isUser && (
                    <div className="mt-3 pt-3 border-t border-border flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="flex items-center gap-2">
                        {msg.confidence === 'high' ? (
                          <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 font-medium">
                            <ShieldCheck className="h-3.5 w-3.5" />
                            {t('chat.verified')}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400 font-medium">
                            <HelpCircle className="h-3.5 w-3.5" />
                            {t('chat.generalGuidance')}
                          </span>
                        )}
                      </div>

                      {/* Text-to-Speech Button */}
                      <button
                        type="button"
                        onClick={() => toggleSpeak(msg.content, msgId)}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold transition ${
                          isThisSpeaking
                            ? 'bg-primary text-white animate-pulse'
                            : 'bg-slate-100 dark:bg-slate-800 text-foreground hover:bg-slate-200 dark:hover:bg-slate-700'
                        }`}
                        title={isThisSpeaking ? 'Stop reading' : 'Read aloud'}
                      >
                        {isThisSpeaking ? (
                          <>
                            <VolumeX className="h-3.5 w-3.5 text-white" />
                            <span>Stop Audio</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="h-3.5 w-3.5 text-primary" />
                            <span>Read Aloud</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}

                  {/* Sources List */}
                  {!isUser && msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2.5 space-y-1 bg-slate-50 dark:bg-[#1C2128] p-2.5 rounded-xl border border-border text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground block mb-1">Official References:</span>
                      {msg.sources.map((src, sIdx) => (
                        <div key={sIdx} className="flex items-center gap-1.5 truncate">
                          <ExternalLink className="h-3 w-3 text-primary shrink-0" />
                          {src.url ? (
                            <a
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline truncate"
                            >
                              {src.title || src.url}
                            </a>
                          ) : (
                            <span className="truncate">{src.title}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Real-time Listening Wave & Interim Transcript */}
          {isListening && (
            <div className="flex items-center gap-3 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-700 dark:text-emerald-300 text-xs animate-in fade-in">
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-4 bg-emerald-500 animate-pulse rounded-full" />
                <span className="w-1.5 h-6 bg-emerald-500 animate-pulse delay-75 rounded-full" />
                <span className="w-1.5 h-3 bg-emerald-500 animate-pulse delay-150 rounded-full" />
              </div>
              <span className="font-semibold">{t('chat.listening')}</span>
              {interimTranscript && (
                <span className="italic text-foreground-muted truncate">&ldquo;{interimTranscript}&rdquo;</span>
              )}
            </div>
          )}

          {isTranscribing && (
            <div className="flex items-center gap-2.5 p-3 bg-primary/10 border border-primary/20 rounded-xl text-primary text-xs animate-pulse">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span className="font-semibold">Transcribing with Sarvam AI...</span>
            </div>
          )}

          {sttError && (
            <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-600 dark:text-rose-400 text-xs font-medium">
              {sttError}
            </div>
          )}

          {loading && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground p-3 bg-white dark:bg-[#161B22] border border-border rounded-2xl w-fit">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span>Analyzing government rules & financial benchmarks...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Sample Prompt Chips (Visible when chat is short) */}
        {messages.length <= 2 && (
          <div className="mb-3 shrink-0">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold mb-2">
              <Lightbulb className="h-3.5 w-3.5 text-amber-500" />
              <span>Suggested Inquiries:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {sampleList.map((prompt, pIdx) => (
                <button
                  key={pIdx}
                  onClick={() => handleSend(prompt)}
                  className="text-xs text-left bg-white dark:bg-[#161B22] border border-border hover:border-primary/50 text-foreground px-3 py-1.5 rounded-full transition shadow-subtle hover:bg-slate-50 dark:hover:bg-[#1C2128]"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Bar with Prominent Voice Mic Button */}
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-center gap-2 bg-white dark:bg-[#161B22] border border-border p-2 rounded-2xl shadow-subtle shrink-0"
        >
          {/* Voice Microphone Toggle */}
          <button
            type="button"
            onClick={handleMicClick}
            disabled={!isSTTSupported || isTranscribing}
            className={`p-3 rounded-xl transition-all relative flex items-center justify-center ${
              isListening
                ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/30 animate-pulse'
                : isTranscribing
                ? 'bg-amber-500 text-white'
                : 'bg-primary/10 text-primary hover:bg-primary/20 border border-primary/20'
            }`}
            title={isListening ? t('chat.stopMic') : t('chat.startMic')}
          >
            {isTranscribing ? (
              <Loader2 className="h-5 w-5 animate-spin text-white" />
            ) : isListening ? (
              <MicOff className="h-5 w-5 text-white" />
            ) : (
              <Mic className="h-5 w-5" />
            )}
            {isListening && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-rose-500"></span>
              </span>
            )}
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isListening
                ? 'Listening... speak in Hindi, Marathi, or English'
                : isTranscribing
                ? 'Transcribing audio with Sarvam AI...'
                : t('chat.placeholder')
            }
            disabled={loading}
            className="flex-1 bg-transparent border-none text-sm text-foreground placeholder:text-muted-foreground focus:outline-none px-2"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="p-3 bg-primary text-white rounded-xl shadow-fintech-btn hover:bg-primary-600 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
          </button>
        </form>
      </main>
    </AppShell>
  );
}
