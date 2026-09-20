import React from "react";

const ReviewCard = ({ review }) => {

  return (
    <div
      style={{
        backgroundColor: "#1e1e1e",
        color: "white",
        padding: "20px",
        borderRadius: "10px",
        marginBottom: "20px",
        border: "1px solid #333",
        boxShadow: "0 2px 10px rgba(0,0,0,0.3)"
      }}
    >

      <h2
        style={{
          marginBottom: "15px",
          color: "#4CAF50"
        }}
      >
        📄 Code Review
      </h2>

      <p style={{ marginBottom: "8px" }}>
        💻 <strong>Language:</strong>
        {" "}
        {review.language}
      </p>

      <p style={{ marginBottom: "8px" }}>
        📝 <strong>Summary:</strong>
        {" "}
        {review.summary}
      </p>

      <p
        style={{
          color: "#999",
          fontSize: "14px",
          marginBottom: "15px"
        }}
      >
        🕒
        {" "}
        {
          review.createdAt
            ? new Date(
              review.createdAt
            ).toLocaleString()
            : "No Date"
        }
      </p>

      {/* ✅ Issues Section */}

      <div>

        <h3 style={{ color: "#ff9800" }}>
          ⚠️ Issues Found:
          {" "}
          {review.issues?.length || 0}
        </h3>

        <div
          style={{
            display: "flex",
            gap: "15px",
            marginBottom: "15px",
            fontWeight: "bold"
          }}
        >

          <p style={{ color: "#ff4d4d" }}>
            High:
            {" "}
            {
              review.issues?.filter(
                i => i.severity === "high"
              ).length
            }
          </p>

          <p style={{ color: "#ffa500" }}>
            Medium:
            {" "}
            {
              review.issues?.filter(
                i => i.severity === "medium"
              ).length
            }
          </p>

          <p style={{ color: "#4CAF50" }}>
            Low:
            {" "}
            {
              review.issues?.filter(
                i => i.severity === "low"
              ).length
            }
          </p>

        </div>

        {
          review.issues?.length === 0 ? (

            <p style={{ color: "#4CAF50" }}>
              ✅ No issues detected
            </p>

          ) : (

            review.issues.map((issue, index) => (

              <div
                key={index}
                style={{
                  backgroundColor: "#2a2a2a",
                  padding: "10px",
                  borderRadius: "8px",
                  marginBottom: "10px",
                  borderLeft:
                    issue.severity === "high"
                      ? "5px solid #ff4d4d"
                      : issue.severity === "medium"
                        ? "5px solid #ffa500"
                        : "5px solid #4CAF50"
                }}
              >

                <p>
                  <strong>Line:</strong>
                  {" "}
                  {issue.line}
                </p>

                <p>
                  <strong>Issue:</strong>
                  {" "}
                  {issue.issue}
                </p>

                <p>
                  <strong>Suggestion:</strong>
                  {" "}
                  {issue.suggestion}
                </p>

                <p
                  style={{
                    fontWeight: "bold",
                    color:
                      issue.severity === "high"
                        ? "#ff4d4d"
                        : issue.severity === "medium"
                          ? "#ffa500"
                          : "#4CAF50"
                  }}
                >
                  Severity:
                  {" "}
                  {issue.severity?.toUpperCase()}
                </p>

              </div>

            ))
          )
        }

      </div>

      {/* ✅ Improved Code */}

      {
        review.improved_code && (

          <div>

            <h3 style={{ color: "#00e676" }}>
              ✅ Improved Code
            </h3>

            <pre
              style={{
                backgroundColor: "#111",
                padding: "15px",
                borderRadius: "8px",
                overflowX: "auto",
                border: "1px solid #333"
              }}
            >
              {review.improved_code}
            </pre>

          </div>

        )
      }

    </div>
  );
};

export default ReviewCard;