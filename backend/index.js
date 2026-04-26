/**
 * Fluex Backend — Emergency Alert Dispatch Server
 * Node.js + Express + Twilio
 */

const express    = require("express");
const mongoose   = require("mongoose");
const cors       = require("cors");
const helmet     = require("helmet");
require("dotenv").config();

const emergencyRoutes = require("./routes/emergency");
const authRoutes      = require("./routes/auth");
const { rateLimiter } = require("./middleware/rateLimiter");

const app  = express();
const PORT = process.env.PORT || 3001;

// ─── Middleware ────────────────────────────────────────────────────────────────
app.use(helmet());
app.use(cors({ origin: process.env.ALLOWED_ORIGINS?.split(",") || "*" }));
app.use(express.json({ limit: "10kb" }));
app.use(rateLimiter);

// ─── Routes ───────────────────────────────────────────────────────────────────
app.use("/api/auth",      authRoutes);
app.use("/api/emergency", emergencyRoutes);

app.get("/health", (_req, res) => res.json({ status: "ok" }));

// ─── Error handler ────────────────────────────────────────────────────────────
app.use((err, _req, res, _next) => {
    console.error("[ERR]", err.message);
    res.status(err.status || 500).json({ error: err.message || "Internal server error" });
});

// ─── Start ────────────────────────────────────────────────────────────────────
mongoose
    .connect(process.env.MONGODB_URI)
    .then(() => {
        console.log("[DB] MongoDB connected");
        app.listen(PORT, () => console.log(`[SERVER] Listening on :${PORT}`));
    })
    .catch((err) => {
        console.error("[DB] Connection failed:", err.message);
        process.exit(1);
    });
