"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

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
        text: `Hello${patientName ? ` ${patientName}` : ''}! My name is Sage, and I'm here to help gather information to prepare for your upcoming visit at Pound of Cure Weight Loss. This conversation will take between 10-30 minutes and will help our team provide you with the best possible care.

Before we begin, I'll need you to have the following items available:
• Your insurance card
• Driver's license or photo ID
• A list of your current medications
• Information about any doctors you see regularly
• Any other health information you think our team should know

You can stop at any time and return to this same link to continue where you left off. 

Let's get started!`,
        sender: "sage",
        timestamp: new Date()
      };

      setMessages([greeting]);
      setSessionStatus("active");
      
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
    } catch (error) {
      console.error("Failed to send message:", error);
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        text: "I'm sorry, I encountered an issue processing your message. Please call our office at 520-298-3300 for assistance.",
        sender: "sage",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
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
                    className={`max-w-[80%] p-3 rounded-lg ${
                      message.sender === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{message.text}</p>
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
            </div>
            
            <div className="border-t p-4">
              <div className="flex space-x-2">
                <Textarea
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
