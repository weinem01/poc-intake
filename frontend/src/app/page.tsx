"use client";

// import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, useRef, Suspense, useCallback } from "react";
import Image from "next/image";
import Lottie from "lottie-react";
import loadingAnimation from "../../graphics/cropped loading animation.json";

interface Message {
  id: string;
  text: string;
  sender: "user" | "sage";
  timestamp: Date;
}

function ChatbotPageContent() {
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change and auto-focus textarea
  useEffect(() => {
    // Immediate scroll for better responsiveness
    scrollToBottom();
    
    // Also scroll after a short delay to handle any async rendering
    const timeoutId = setTimeout(() => {
      scrollToBottom();
      textareaRef.current?.focus();
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, [messages, isLoading]);

  // Session initialization
  const initializeSession = useCallback(async () => {
    try {
      setIsInitializing(true);
      setSessionError(null);

      // Get the encoded ID from the URL
      const encodedId = searchParams.get('id');
      if (!encodedId) {
        throw new Error('No session ID provided in URL');
      }

      // Decode the base64 MRN
      const mrn = atob(encodedId);
      
      // Call the backend to initialize/get session
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/sessions/init`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mrn }),
      });

      if (!response.ok) {
        throw new Error(`Failed to initialize session: ${response.status}`);
      }

      const data = await response.json();
      setSessionId(data.session_id);
      
    } catch (error) {
      console.error('Session initialization error:', error);
      setSessionError(error instanceof Error ? error.message : 'Failed to initialize session');
    } finally {
      setIsInitializing(false);
    }
  }, [searchParams]);

  // Initialize session and add welcome message after hydration
  useEffect(() => {
    // Add welcome message after component mounts (client-side only)
    setMessages([{
      id: "welcome",
      text: `<p>Hello! My name is <strong>Sage</strong>, I'm <strong>AI powered</strong> and I'm here to help gather information to prepare for your upcoming visit at <strong>Pound of Cure Weight Loss</strong>. This conversation will take between <strong>10-30 minutes</strong> and will help our team provide you with the best possible care.</p>
<p style="margin-top: 8px;">Before we begin, I'll need you to have the following items available:</p>
<ul style="list-style-type: disc; padding-left: 20px; margin: 6px 0;">
  <li>Your insurance card</li>
  <li>Driver's license or photo ID</li>
  <li>A list of your current medications</li>
  <li>Information about any doctors you see regularly</li>
  <li>Any other health information you think our team should know</li>
</ul>
<p style="margin-top: 8px;"><em>You can stop at any time and return to this same link to continue where you left off.</em></p>
<p style="margin-top: 8px;"><strong>To get started, please confirm your <em>date of birth and last name</em> for verification purposes.</strong></p>`,
      sender: "sage",
      timestamp: new Date()
    }]);
    
    // Ensure welcome message is visible
    setTimeout(() => scrollToBottom(), 200);
    
    initializeSession();
  }, [initializeSession]);

  // Focus textarea when session is ready
  useEffect(() => {
    if (sessionId && !isInitializing) {
      textareaRef.current?.focus();
    }
  }, [sessionId, isInitializing]);

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      // Use requestAnimationFrame to ensure DOM is fully rendered
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ 
          behavior: "smooth",
          block: "end",
          inline: "nearest"
        });
      });
    }
  };

  const formatMessageText = (text: string) => {
    // Convert bullet points to proper HTML with line breaks
    return text
      .replace(/• /g, '<br/>• ')  // Add line break before each bullet
      .replace(/^<br\/>/, '')    // Remove leading line break if it exists
      .replace(/\n/g, '<br/>');  // Convert any remaining newlines to HTML breaks
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading || !sessionId) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}-user`,
      text: currentMessage,
      sender: "user",
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage("");
    setIsLoading(true);
    
    // Scroll to bottom immediately after adding user message
    setTimeout(() => scrollToBottom(), 50);

    try {
      // Call the backend API
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentMessage,
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const sageResponse: Message = {
        id: `msg-${Date.now()}-sage`,
        text: data.response || "I received your message and I'm processing it.",
        sender: "sage",
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, sageResponse]);
      
      // Scroll to bottom after adding sage response
      setTimeout(() => scrollToBottom(), 100);
    } catch (error) {
      console.error('Error calling backend:', error);
      const errorResponse: Message = {
        id: `msg-${Date.now()}-sage`,
        text: "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
        sender: "sage",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorResponse]);
      
      // Scroll to bottom after adding error response
      setTimeout(() => scrollToBottom(), 100);
    } finally {
      setIsLoading(false);
      // Auto-focus textarea after response
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Show loading state during session initialization
  if (isInitializing) {
    return (
      <div className="h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-[#4CAF50] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing your session...</p>
        </div>
      </div>
    );
  }

  // Show error state if session initialization failed
  if (sessionError) {
    return (
      <div className="h-screen bg-white flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Session Error</h2>
          <p className="text-gray-600 mb-4">{sessionError}</p>
          <button 
            onClick={initializeSession}
            className="bg-[#4CAF50] text-white px-4 py-2 rounded-lg hover:bg-[#45a049] transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-white flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-white shadow-sm px-6 py-4 flex items-center justify-end flex-shrink-0">
        <div className="w-10 h-10 bg-[#4CAF50] rounded-full flex items-center justify-center text-white">
          {/* Brain icon */}
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C9.62 2 7.5 3.12 6.03 4.82C4.34 4.36 2.5 4.96 1.47 6.38c-.87 1.21-1.06 2.78-.49 4.17C.37 11.61 0 12.78 0 14c0 2.21 1.79 4 4 4 .73 0 1.41-.2 2-.54V20c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2v-2.54c.59.34 1.27.54 2 .54 2.21 0 4-1.79 4-4 0-1.22-.37-2.39-.98-3.45.57-1.39.38-2.96-.49-4.17-1.03-1.42-2.87-2.02-4.56-1.56C16.5 3.12 14.38 2 12 2zm0 2c2.21 0 4 1.79 4 4 0 .4-.06.78-.17 1.14l-.37 1.34 1.38.17C18.09 10.78 19 11.82 19 13v1c0 1.1-.9 2-2 2h-1v4H8v-4H7c-1.1 0-2-.9-2-2v-1c0-1.18.91-2.22 2.16-2.35l1.38-.17-.37-1.34C8.06 8.78 8 8.4 8 8c0-2.21 1.79-4 4-4z"/>
          </svg>
        </div>
      </header>

      {/* Welcome Section - Fixed */}
      <div className="bg-white shadow-sm mx-4 mt-4 rounded-lg p-6 text-center flex-shrink-0">
        <div className="flex items-center justify-center gap-4 mb-2">
          <div className="w-20 h-20 flex-shrink-0 overflow-hidden rounded-lg">
            <Image 
              src="/head-logo.png" 
              alt="Healthy mind logo" 
              width={80}
              height={80}
              className="w-full h-full object-contain"
              onError={() => {}}
            />
          </div>
          <h2 className="text-2xl font-bold text-gray-800">Welcome to Pound of Cure</h2>
        </div>
        <p className="text-gray-600">
          We&apos;re excited to help you on your weight loss journey. Let&apos;s start with a few questions to get to know you better.
        </p>
      </div>

      {/* Messages Area - Only Scrollable Section */}
      <div className="flex-1 overflow-y-auto px-4 py-6 bg-white min-h-0">
          <div className="max-w-3xl mx-auto" style={{ gap: '12px', display: 'flex', flexDirection: 'column' }}>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div className={`flex max-w-[75%] ${message.sender === "user" ? "flex-row-reverse" : ""}`}>
                  {/* Avatar - Only for Sage */}
                  {message.sender === "sage" && (
                    <div className="flex-shrink-0 mt-1 mr-3">
                      <div className="w-10 h-10 rounded-full bg-gray-500 flex items-center justify-center text-white">
                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2C9.62 2 7.5 3.12 6.03 4.82C4.34 4.36 2.5 4.96 1.47 6.38c-.87 1.21-1.06 2.78-.49 4.17C.37 11.61 0 12.78 0 14c0 2.21 1.79 4 4 4 .73 0 1.41-.2 2-.54V20c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2v-2.54c.59.34 1.27.54 2 .54 2.21 0 4-1.79 4-4 0-1.22-.37-2.39-.98-3.45.57-1.39.38-2.96-.49-4.17-1.03-1.42-2.87-2.02-4.56-1.56C16.5 3.12 14.38 2 12 2zm0 2c2.21 0 4 1.79 4 4 0 .4-.06.78-.17 1.14l-.37 1.34 1.38.17C18.09 10.78 19 11.82 19 13v1c0 1.1-.9 2-2 2h-1v4H8v-4H7c-1.1 0-2-.9-2-2v-1c0-1.18.91-2.22 2.16-2.35l1.38-.17-.37-1.34C8.06 8.78 8 8.4 8 8c0-2.21 1.79-4 4-4z"/>
                        </svg>
                      </div>
                    </div>
                  )}
                  
                  {/* Message Bubble */}
                  <div className="flex flex-col">
                    <div
                      className={`rounded-2xl ${
                        message.sender === "user"
                          ? "bg-[#4CAF50] text-white border border-[#45a049]"
                          : "bg-[#eef4f2] text-gray-800 border border-gray-200 shadow-sm"
                      }`}
                      style={{
                        borderTopLeftRadius: message.sender === "sage" ? "4px" : "18px",
                        borderTopRightRadius: message.sender === "user" ? "4px" : "18px",
                        padding: "12px"
                      }}
                    >
                      {message.sender === "sage" ? (
                        <div>
                          <div
                            className="text-sm leading-relaxed"
                            style={{ color: "#374151" }}
                            dangerouslySetInnerHTML={{ __html: formatMessageText(message.text) }}
                          />
                          <p className="text-right mt-2" style={{ fontSize: '10px', color: '#6b7280' }}>
                            {message.timestamp.toLocaleDateString()} {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      ) : (
                        <div>
                          <p className="text-sm leading-relaxed" style={{ color: 'white' }}>{message.text}</p>
                          <p className="text-right mt-2" style={{ fontSize: '10px', color: 'rgba(255, 255, 255, 0.8)' }}>
                            {message.timestamp.toLocaleDateString()} {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {/* Typing Indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex max-w-[75%]">
                  <div className="flex-shrink-0 mt-1 mr-3">
                    <div className="w-10 h-10 rounded-full bg-gray-500 flex items-center justify-center text-white">
                      <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2C9.62 2 7.5 3.12 6.03 4.82C4.34 4.36 2.5 4.96 1.47 6.38c-.87 1.21-1.06 2.78-.49 4.17C.37 11.61 0 12.78 0 14c0 2.21 1.79 4 4 4 .73 0 1.41-.2 2-.54V20c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2v-2.54c.59.34 1.27.54 2 .54 2.21 0 4-1.79 4-4 0-1.22-.37-2.39-.98-3.45.57-1.39.38-2.96-.49-4.17-1.03-1.42-2.87-2.02-4.56-1.56C16.5 3.12 14.38 2 12 2zm0 2c2.21 0 4 1.79 4 4 0 .4-.06.78-.17 1.14l-.37 1.34 1.38.17C18.09 10.78 19 11.82 19 13v1c0 1.1-.9 2-2 2h-1v4H8v-4H7c-1.1 0-2-.9-2-2v-1c0-1.18.91-2.22 2.16-2.35l1.38-.17-.37-1.34C8.06 8.78 8 8.4 8 8c0-2.21 1.79-4 4-4z"/>
                      </svg>
                    </div>
                  </div>
                  <div className="bg-[#eef4f2] border border-gray-200 shadow-sm rounded-2xl" style={{ borderTopLeftRadius: "4px", padding: "12px" }}>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-600">Thinking</span>
                      <div style={{ width: '100px', height: '100px', overflow: 'hidden' }}>
                        <Lottie 
                          animationData={loadingAnimation}
                          loop={true}
                          autoplay={true}
                          style={{ width: '100px', height: '100px' }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
      </div>

      {/* Fixed Input Area at Bottom */}
      <div className="bg-white px-4 pt-4 pb-3 flex-shrink-0" style={{ paddingBottom: '12px' }}>
        <div className="max-w-3xl mx-auto">
          <div className="flex items-stretch" style={{ padding: '2px' }}>
            <Textarea
              ref={textareaRef}
              value={currentMessage}
              onChange={(e) => setCurrentMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={sessionId ? "Type your message here..." : "Initializing session..."}
              className="flex-1 bg-[#f5f7fa] border border-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-[#4CAF50] focus:border-transparent text-sm leading-relaxed min-h-[48px] max-h-32"
              rows={1}
              disabled={isLoading || !sessionId}
              style={{
                overflow: 'auto',
                maxHeight: '128px',
                marginRight: '12px',
                borderRadius: '8px',
                padding: '8px'
              }}
            />
            <button
              type="button"
              onClick={sendMessage}
              disabled={!currentMessage.trim() || isLoading || !sessionId}
              className="flex-shrink-0 w-[100px] md:w-[150px] bg-[#4CAF50] hover:bg-[#45a049] active:bg-[#388E3C] font-medium transition-all shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#4CAF50] focus:ring-offset-2 flex items-center justify-center disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ minHeight: '48px', borderRadius: '8px', fontSize: '18px', color: 'white' }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChatbotPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#f5f7fa] flex items-center justify-center">Loading...</div>}>
      <ChatbotPageContent />
    </Suspense>
  );
}