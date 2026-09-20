const dns = require("node:dns");
dns.setServers(["8.8.8.8", "1.1.1.1"]);

const express = require("express");
const cors = require("cors");
const axios = require("axios");
const mongoose = require("mongoose");
require("dotenv").config();

const Review = require("./models/Review");

const app = express();

app.use(cors());

/* =========================
   ✅ Limit Request Size
========================= */
app.use(express.json({ limit: "1mb" }));

const PORT = 5000;

/* =========================
   ✅ Validate AI Response
========================= */
function validateAIResponse(data) {

  return (
    data &&
    typeof data.summary === "string" &&
    Array.isArray(data.issues) &&
    typeof data.improved_code === "string"
  );

}

/* =========================
   ✅ MongoDB Connection
========================= */
mongoose.connect(process.env.MONGO_URI)

  .then(() => {
    console.log("MongoDB Connected ✅");
  })

  .catch((err) => {
    console.log("MongoDB Error ❌", err);
  });

/* =========================
   ✅ Logging Middleware
========================= */
app.use((req, res, next) => {

  console.log(
    `${new Date().toISOString()} - ${req.method} ${req.url}`
  );

  next();

});

/* =========================
   ✅ Routes
========================= */

// Root
app.get("/", (req, res) => {

  res.send("Backend is running");

});

// Health
app.get("/health", (req, res) => {

  res.json({
    status: "OK"
  });

});

/* =========================
   ✅ AI Review Route
========================= */
app.post("/review", async (req, res) => {

  const { code, language } = req.body;

  /* =========================
     ✅ Input Validation
  ========================= */
  if (!code || code.trim() === "") {

    return res.status(400).json({
      success: false,
      summary: "No code provided",
      issues: [],
      improved_code: ""
    });

  }

  /* =========================
     ✅ Code Size Protection
  ========================= */
  if (code.length > 5000) {

    return res.status(400).json({
      success: false,
      summary: "Code exceeds limit",
      issues: [],
      improved_code: ""
    });

  }

  try {

    const aiResponse = await axios.post(

      "http://127.0.0.1:8000/review",

      {
        code,
        language
      },

      {
        timeout: 20000
      }

    );

    const data = aiResponse.data;

    /* =========================
       ✅ Validate AI Structure
    ========================= */
    if (!validateAIResponse(data)) {

      return res.status(500).json({
        success: false,
        summary: "Invalid AI response structure",
        issues: [],
        improved_code: ""
      });

    }

    /* =========================
       ✅ AI Error Check
    ========================= */
    if (!data || data.error) {

      return res.status(500).json({
        success: false,
        summary: "AI failed",
        issues: [],
        improved_code: "",
        error: data?.error || "Unknown error"
      });

    }

    /* =========================
       ✅ Success Response
    ========================= */
    return res.json({
      success: true,
      summary: data.summary,
      issues: data.issues,
      improved_code: data.improved_code
    });

  } catch (error) {

    console.error("Error ❌:", error.message);

    return res.status(500).json({
      success: false,
      summary: "AI service error",
      issues: [],
      improved_code: "",
      error: error.message
    });

  }

});

/* =========================
   ✅ Save Review Route
========================= */
app.post("/reviews", async (req, res) => {

  try {

    const {
      code,
      language,
      summary,
      issues,
      improved_code
    } = req.body;

    /* =========================
       ✅ Required Validation
    ========================= */
    if (!code || code.trim() === "") {

      return res.status(400).json({
        success: false,
        error: "Code is required"
      });

    }

    /* =========================
       ✅ Save Review
    ========================= */
    await Review.create({

      code,

      language,

      summary,

      issues,

      improved_code

    });

    res.status(201).json({
      success: true,
      message: "Review saved successfully"
    });

  } catch (error) {

    console.error("Save Error ❌:", error.message);

    res.status(500).json({
      success: false,
      error: error.message
    });

  }

});

/* =========================
   ✅ Fetch Saved Reviews
========================= */
app.get("/reviews", async (req, res) => {

  try {

    const page = parseInt(req.query.page) || 1;

    const limit = 10;

    const skip = (page - 1) * limit;

    const reviews = await Review.find()

      .sort({ createdAt: -1 })

      .skip(skip)

      .limit(limit);

    res.json(reviews);

  } catch (error) {

    console.error("Fetch Error ❌:", error.message);

    res.status(500).json({
      success: false,
      error: error.message
    });

  }

});

/* =========================
   ✅ Delete Review
========================= */
app.delete("/reviews/:id", async (req, res) => {

  try {

    await Review.findByIdAndDelete(req.params.id);

    res.json({
      success: true,
      message: "Review deleted successfully"
    });

  } catch (error) {

    console.error("Delete Error ❌:", error.message);

    res.status(500).json({
      success: false,
      error: error.message
    });

  }

});

/* =========================
   ✅ Start Server
========================= */
app.listen(PORT, () => {

  console.log(`Server running on port ${PORT}`);

});