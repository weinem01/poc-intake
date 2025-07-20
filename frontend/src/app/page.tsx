"use client";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, useRef, Suspense } from "react";

interface Message {
  id: string;
  text: string;
  sender: "user" | "sage";
  timestamp: Date;
}

function ChatbotPageContent() {
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      text: `<p>Hello! My name is <strong>Sage</strong>, I'm <strong>AI powered</strong> and I'm here to help gather information to prepare for your upcoming visit at <strong>Pound of Cure Weight Loss</strong>. This conversation will take between <strong>10-30 minutes</strong> and will help our team provide you with the best possible care.</p>

<p style="margin-top: 16px;">Before we begin, I'll need you to have the following items available:</p>
<ul style="list-style-type: disc; padding-left: 20px; margin: 10px 0;">
  <li>Your insurance card</li>
  <li>Driver's license or photo ID</li>
  <li>A list of your current medications</li>
  <li>Information about any doctors you see regularly</li>
  <li>Any other health information you think our team should know</li>
</ul>

<p style="margin-top: 16px;"><em>You can stop at any time and return to this same link to continue where you left off.</em></p>

<p style="margin-top: 20px;"><strong>To get started, please confirm your <em>date of birth and last name</em> for verification purposes.</strong></p>`,
      sender: "sage",
      timestamp: new Date()
    }
  ]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when messages change and auto-focus textarea
  useEffect(() => {
    setTimeout(() => {
      scrollToBottom();
      textareaRef.current?.focus();
    }, 100);
  }, [messages, isLoading]);

  // Focus textarea on component mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}-user`,
      text: currentMessage,
      sender: "user",
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage("");
    setIsLoading(true);

    // Simulate response (since backend is not connected)
    setTimeout(() => {
      const sageResponse: Message = {
        id: `msg-${Date.now()}-sage`,
        text: "Thank you for your message! I'm processing your information.",
        sender: "sage",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, sageResponse]);
      setIsLoading(false);
      // Auto-focus textarea after response
      setTimeout(() => textareaRef.current?.focus(), 100);
    }, 1000);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

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
            <img 
              src="/head-logo.png" 
              alt="Healthy mind logo" 
              className="w-full h-full object-contain"
              style={{ maxWidth: '80px', maxHeight: '80px' }}
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
          </div>
          <h2 className="text-2xl font-bold text-gray-800">Welcome to Pound of Cure</h2>
        </div>
        <p className="text-gray-600">
          We're excited to help you on your weight loss journey. Let's start with a few questions to get to know you better.
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
                            className="prose prose-sm max-w-none"
                            style={{ color: "#374151" }}
                            dangerouslySetInnerHTML={{ __html: message.text }}
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
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
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
              placeholder="Type your message here..."
              className="flex-1 bg-[#f5f7fa] border border-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-[#4CAF50] focus:border-transparent text-sm leading-relaxed min-h-[48px] max-h-32"
              rows={1}
              disabled={isLoading}
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
              disabled={!currentMessage.trim() || isLoading}
              className="flex-shrink-0 w-[100px] md:w-[150px] bg-[#4CAF50] hover:bg-[#45a049] active:bg-[#388E3C] font-medium transition-all shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-[#4CAF50] focus:ring-offset-2 flex items-center justify-center"
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