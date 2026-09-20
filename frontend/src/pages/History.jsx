import React, { useEffect, useState } from "react";
import axios from "axios";
import ReviewCard from "../components/ReviewCard";

const History = () => {

  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReviews();
  }, []);

  const fetchReviews = async () => {

    try {

      const response = await axios.get(
        "http://localhost:5000/reviews"
      );

      setReviews(response.data);

    } catch (error) {

      console.error(
        "Error fetching reviews:",
        error
      );

    } finally {

      setLoading(false);
    }
  };

  return (
    <div
      style={{
        padding: "20px",
        maxWidth: "1000px",
        margin: "auto",
        backgroundColor: "#121212",
        minHeight: "100vh",
        color: "white"
      }}
    >

      <h1
        style={{
          textAlign: "center",
          marginBottom: "30px",
          color: "#4CAF50"
        }}
      >
        📜 Review History
      </h1>

      {loading ? (

        <p
          style={{
            textAlign: "center",
            fontSize: "18px"
          }}
        >
          Loading reviews...
        </p>

      ) : reviews.length === 0 ? (

        <p
          style={{
            textAlign: "center",
            color: "#999",
            fontSize: "18px"
          }}
        >
          No review history found.
        </p>

      ) : (

        reviews.map((review) => (

          <ReviewCard
            key={review._id}
            review={review}
          />

        ))
      )}

    </div>
  );
};

export default History;