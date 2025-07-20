"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useSearchParams } from "next/navigation";
import { useEffect, useState, useRef } from "react";

interface Message {
  id: string;
  text: string;
  sender: "user" | "sage";
  timestamp: Date;
}

export default function ChatbotPage() {
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [patientMRN, setPatientMRN] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<"initializing" | "active" | "error">("initializing");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const id = searchParams.get("id");
    if (id) {
      try {
        const decodedMRN = atob(id);
        setPatientMRN(decodedMRN);
        initializeSession(decodedMRN);
      } catch (error) {
        console.error("Failed to decode MRN:", error);
        setSessionStatus("error");
        setMessages([{
          id: "error",
          text: "Invalid session link. Please call our office at 520-298-3300 for assistance.",
          sender: "sage",
          timestamp: new Date()
        }]);
      }
    } else {
      setSessionStatus("error");
      setMessages([{
        id: "error",
        text: "No patient identifier provided. Please use the link provided by your care team or call our office at 520-298-3300.",
        sender: "sage",
        timestamp: new Date()
      }]);
    }
  }, [searchParams]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const initializeSession = async (mrn: string) => {
    try {
      setIsLoading(true);

      // Call backend to initialize session
      const response = await fetch('http://localhost:8000/api/v1/sessions/init', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mrn }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to initialize session');
      }

      const sessionData = await response.json();

      // Store session ID for future requests
      sessionStorage.setItem('intake_session_id', sessionData.session_id);

      // Add initial greeting with personalized message
      const patientName = sessionData.patient_data?.first_name || '';
      const greeting: Message = {
        id: `msg-${Date.now()}`,
        text: `<p>Hello${patientName ? ` ${patientName}` : ''}! My name is <strong>Sage</strong>, I'm <strong>AI powered</strong> and I'm here to help gather information to prepare for your upcoming visit at <strong>Pound of Cure Weight Loss</strong>. This conversation will take between <strong>10-30 minutes</strong> and will help our team provide you with the best possible care.</p>

<p>Before we begin, I'll need you to have the following items available:</p>
<ul style="list-style-type: disc; padding-left: 20px; margin: 10px 0;">
  <li>Your insurance card</li>
  <li>Driver's license or photo ID</li>
  <li>A list of your current medications</li>
  <li>Information about any doctors you see regularly</li>
  <li>Any other health information you think our team should know</li>
</ul>

<p><em>You can stop at any time and return to this same link to continue where you left off.</em></p>

<p style="margin-top: 20px;"><strong>To get started, please confirm your <em>date of birth and last name</em> for verification purposes.</strong></p>`,
        sender: "sage",
        timestamp: new Date()
      };

      setMessages([greeting]);
      setSessionStatus("active");
      
      // Focus textarea after initial greeting
      setTimeout(() => textareaRef.current?.focus(), 100);

    } catch (error) {
      console.error("Session initialization failed:", error);
      setSessionStatus("error");
      setMessages([{
        id: "error",
        text: error instanceof Error ? error.message : "Unable to initialize your session. Please call our office at 520-298-3300 for assistance.",
        sender: "sage",
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
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

    // Scroll immediately after adding user message
    setTimeout(scrollToBottom, 100);

    try {
      const sessionId = sessionStorage.getItem('intake_session_id');
      if (!sessionId) {
        throw new Error('No active session found');
      }

      // Call backend chat API with LangChain agent
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentMessage,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to process message');
      }

      const chatResponse = await response.json();

      const sageResponse: Message = {
        id: `msg-${Date.now()}-sage`,
        text: chatResponse.response,
        sender: "sage",
        timestamp: new Date()
      };

      setMessages(prev => [...prev, sageResponse]);
      
      // Scroll to bottom and focus textarea after bot response
      setTimeout(() => {
        scrollToBottom();
        textareaRef.current?.focus();
      }, 100);
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        text: "I'm sorry, I encountered an issue processing your message. Please call our office at 520-298-3300 for assistance.",
        sender: "sage",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Scroll to bottom and focus textarea after error message
      setTimeout(() => {
        scrollToBottom();
        textareaRef.current?.focus();
      }, 100);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (sessionStatus === "error") {
    return (
      <div className="min-h-screen bg-secondary flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle className="text-center text-destructive">Session Error</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {messages.map((message) => (
                <div key={message.id} className="text-center text-muted-foreground">
                  {message.text}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-secondary">
      <div className="container mx-auto p-4 h-screen flex flex-col">
        <Card className="flex-1 flex flex-col">
          <CardHeader className="bg-primary text-primary-foreground">
            <CardTitle className="text-center">
              Pound of Cure Weight Loss - Patient Intake
            </CardTitle>
            <p className="text-center text-sm opacity-90">
              Powered by Sage AI Assistant
            </p>
          </CardHeader>

          <CardContent className="flex-1 flex flex-col p-0">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] p-3 rounded-lg ${message.sender === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                      }`}
                  >
                    {message.sender === "sage" ? (
                      <div
                        className="prose prose-sm max-w-none text-muted-foreground"
                        dangerouslySetInnerHTML={{ __html: message.text }}
                      />
                    ) : (
                      <p className="whitespace-pre-wrap">{message.text}</p>
                    )}
                    <p className="text-xs opacity-70 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-muted text-muted-foreground p-3 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <div className="animate-pulse">Sage is typing...</div>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t p-4">
              <div className="flex space-x-2">
                <Textarea
                  ref={textareaRef}
                  value={currentMessage}
                  onChange={(e) => setCurrentMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message here..."
                  className="resize-none"
                  rows={2}
                  disabled={isLoading}
                />
                <Button
                  onClick={sendMessage}
                  disabled={!currentMessage.trim() || isLoading}
                  className="self-end"
                >
                  Send
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
