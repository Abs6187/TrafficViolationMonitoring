const mongoose = require("mongoose");

const mongoUri = process.env.MONGODB_URI || "mongodb://127.0.0.1:27017/mlProject";

mongoose
  .connect(mongoUri)
  .then(() => {
    console.log("MongoDB connected");
  })
  .catch((error) => {
    console.error("MongoDB connection failed:", error.message);
  });

const UserSchema = new mongoose.Schema({
  numberplate: {
    type: String,
    required: true,
  },
  email: {
    type: String,
    default: "",
  },
  phonenumber: {
    type: String,
    default: "",
  },
});

const User = mongoose.model("UserTable", UserSchema);

module.exports = {
  User,
};
