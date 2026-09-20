import React, { useState } from "react";
import Editor from "@monaco-editor/react";
// We use the service import for cleaner code
import { reviewCode } from "./services/api";

function App() {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("javascript");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleReview = async () => {
    if (!code.trim()) {
      alert("Please enter code first!");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await reviewCode(code, language);

      try {
        const parsed =
          typeof data === "string"
            ? JSON.parse(data)
            : data;

        setResult(parsed);

      } catch {
        setResult(data);
      }

    } catch (error) {
      console.error(error);
      setError("Error reviewing code ❌. Make sure your backend is running on port 5000.");
      setResult(null);

    } finally {
      setLoading(false);
    }
  };

  const saveReview = async () => {

    try {

      if (code.length > 5000) {
        alert("Code too large ❌");
        return;
      }

      await fetch(
        "http://localhost:5000/reviews",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            fileName: "User Code",

            code,

            language,

            summary:
              result.summary || "No summary",

            score:
              result.score || 7,

            issues:
              result.issues || [],

            improved_code:
              result.improved_code || "",

            createdAt: new Date(),
          }),
        }
      );

      alert(
        "Review saved successfully ✅"
      );

    } catch (error) {

      console.error(error);

      alert(
        "Failed to save review ❌"
      );
    }
  };

  return (
    <div style={{
      padding: "20px",
      maxWidth: "1000px",
      margin: "auto",
      textAlign: "center",
      backgroundColor: "#121212",
      color: "white",
      minHeight: "100vh"
    }}>
      <h1>AI Code Reviewer</h1>

      <button
        onClick={() => window.location.href = "/history"}
        style={{
          padding: "10px 20px",
          backgroundColor: "#2196F3",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
          marginBottom: "20px",
          fontSize: "16px"
        }}
      >
        📜 View History
      </button>

      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        style={{ padding: "5px", marginBottom: "20px" }}
      >
        <option value="javascript">JavaScript</option>
        <option value="python">Python</option>
        <option value="java">Java</option>
      </select>

      <Editor
        height="400px"
        width="100%"
        language={language}
        theme="vs-dark"
        value={code}
        options={{
          fontSize: 16,
          minimap: { enabled: false },
          padding: { top: 10 }
        }}
        onChange={(value) => setCode(value || "")}
      />

      <br />

      <button onClick={handleReview}
        disabled={loading}
        style={{
          marginTop: "20px",
          padding: "10px 20px",
          backgroundColor: loading ? "#555" : "#4CAF50",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: loading ? "not-allowed" : "pointer",
          fontSize: "16px"
        }}
      >
        {loading ? "Analysing with AI..." : "Review Code"}
      </button>

      {error && <p style={{ color: "#ff4d4d", marginTop: "10px" }}>{error}</p>}

      {result && (
        <div style={{ marginTop: "20px", textAlign: "left" }}>
          <h2>
            📊 Analysis Result
            <span style={{
              marginLeft: "10px",
              fontSize: "14px",
              background: "#333",
              padding: "4px 10px",
              borderRadius: "6px",
            }}>{language.toUpperCase()}
            </span>

          </h2>

          <button
            onClick={saveReview}
            style={{
              marginTop: "15px",
              padding: "10px 20px",
              backgroundColor: "#2196F3",
              color: "white",
              border: "none",
              borderRadius: "5px",
              cursor: "pointer",
              fontSize: "16px"
            }}
          >
            Save Review
          </button>

          {/* If the AI returns a simple string */}
          {typeof result === "string" && (
            <pre style={{
              background: "#1e1e1e",
              color: "#00ff9f",
              padding: "15px",
              borderRadius: "8px",
              whiteSpace: "pre-wrap",
              border: "1px solid #333"
            }}>
              {result}
            </pre>
          )}

          {/* If the AI returns structured JSON */}
          {typeof result === "object" && (
            <>
              <div style={{ background: "#1e1e1e", padding: "15px", borderRadius: "8px", marginBottom: "15px" }}><strong>Summary:</strong> <p>{result.summary || "No summary available"}</p></div>
              <h3>⚠️ Issues Found: {(result.issues || []).length}</h3>

              {(result.issues || []).length === 0 ? (
                <p style={{ color: "#00c853", fontWeight: "bold" }}>✅ No issues detected - clean code!</p>
              ) : (
                (result.issues || []).map((issue, index) => (
                  <div key={index} style={{
                    background: "#1e1e1e",
                    color: "white",
                    padding: "15px",
                    marginBottom: "10px",
                    borderRadius: "5px",
                    borderLeft: issue.severity === "high" ? "5px solid #ff4d4d" : issue.severity === "medium" ? "5px solid #ffa500" : "5px solid #00c853"
                  }}>
                    <p><strong>Line:</strong> {issue.line}</p>
                    <p><strong>Issue:</strong> {issue.issue}</p>
                    <p><strong>Suggestion:</strong> {issue.suggestion}</p>
                    <p style={{
                      color: issue.severity === "high" ? "#ff4d4d" : issue.severity === "medium" ? "#ffa500" : "#00c853",
                      fontWeight: "bold"
                    }}>
                      Severity: {issue.severity?.toUpperCase()}
                    </p>
                  </div>
                ))
              )}

              {result.improved_code && (
                <>
                  <h3>✅ Improved Code</h3>
                  <pre style={{
                    background: "#1e1e1e",
                    color: "#00ff9f",
                    padding: "15px",
                    borderRadius: "8px",
                    overflowX: "auto",
                    border: "1px solid #333"
                  }}>
                    {result.improved_code}
                  </pre>
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default App;