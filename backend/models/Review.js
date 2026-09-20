const mongoose = require("mongoose");

const reviewSchema = new mongoose.Schema({
  code: {
   type: String,
   required: true,
   maxlength: 5000
},
  language: {
    type: String,
    default: "javascript"
  },
  issues: {
    type: Array,
    default: []
  },
  summary: {
    type: String,
    default: ""
  },
  improved_code: {
    type: String,
    default: ""
  },
  createdAt: {
   type: Date,
   default: Date.now,
   index: true
}
});

module.exports = mongoose.model("Review", reviewSchema);