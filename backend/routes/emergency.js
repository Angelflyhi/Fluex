/**
 * Emergency alert route
 * POST /api/emergency/alert
 *
 * Body: {
 *   deviceId: string,
 *   emergencyScore: number,  // 0–1
 *   location: { lat: number, lng: number } | null,
 *   hr: number,
 *   fallConfidence: number
 * }
 *
 * Flow:
 *   1. Validate device token
 *   2. Look up user's emergency contacts
 *   3. Broadcast Twilio SMS to all contacts
 *   4. Store event in MongoDB
 */

const express   = require("express");
const twilio    = require("twilio");
const Emergency = require("../models/Emergency");
const User      = require("../models/User");
const { verifyDevice } = require("../middleware/auth");

const router = express.Router();

const twilioClient = twilio(
    process.env.TWILIO_ACCOUNT_SID,
    process.env.TWILIO_AUTH_TOKEN
);

// ─────────────────────────────────────────────────────────────────────────────
router.post("/alert", verifyDevice, async (req, res) => {
    const { emergencyScore, location, hr, fallConfidence } = req.body;
    const userId = req.userId;

    try {
        const user = await User.findById(userId).select("emergencyContacts name");
        if (!user) return res.status(404).json({ error: "User not found" });

        const contacts = user.emergencyContacts || [];
        if (contacts.length === 0) {
            return res.status(200).json({ sent: 0, message: "No contacts configured" });
        }

        const locationStr = location
            ? `https://maps.google.com/?q=${location.lat},${location.lng}`
            : "location unavailable";

        const body =
            `🚨 FLUEX EMERGENCY ALERT\n` +
            `${user.name} may need help.\n` +
            `Score: ${(emergencyScore * 100).toFixed(0)}%  HR: ${hr} BPM\n` +
            `Location: ${locationStr}\n` +
            `Reply CANCEL to acknowledge.`;

        const results = await Promise.allSettled(
            contacts.map((number) =>
                twilioClient.messages.create({
                    to:   number,
                    from: process.env.TWILIO_PHONE_NUMBER,
                    body,
                })
            )
        );

        const sent   = results.filter((r) => r.status === "fulfilled").length;
        const failed = results.filter((r) => r.status === "rejected").length;

        // Persist event
        await Emergency.create({
            userId,
            emergencyScore,
            fallConfidence,
            heartRate: hr,
            location,
            contactsNotified: sent,
            timestamp: new Date(),
        });

        return res.json({ sent, failed, message: `Alerted ${sent} contact(s)` });
    } catch (err) {
        console.error("[EMERGENCY]", err.message);
        return res.status(500).json({ error: "Alert dispatch failed" });
    }
});

// GET /api/emergency/history — last 20 events for authenticated user
router.get("/history", verifyDevice, async (req, res) => {
    const events = await Emergency.find({ userId: req.userId })
        .sort({ timestamp: -1 })
        .limit(20)
        .lean();
    res.json(events);
});

module.exports = router;
