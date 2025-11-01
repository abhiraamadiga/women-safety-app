import express from "express";
import fs from "fs";
import path from "path";
import cors from "cors";
import multer from "multer";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

// Create directories if they don't exist
const uploadsDir = path.join(__dirname, "uploads");
const logsDir = path.join(__dirname, "logs");
[uploadsDir, logsDir].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, uploadsDir);
  },
  filename: (req, file, cb) => {
    const uniqueName = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}${path.extname(file.originalname)}`;
    cb(null, uniqueName);
  }
});

const upload = multer({ 
  storage,
  limits: { fileSize: 100 * 1024 * 1024 } // 100MB limit
});

app.use(cors());
app.use(express.json());
app.use(express.static(__dirname));
app.use("/uploads", express.static(uploadsDir));

const sosFile = path.join(logsDir, "sos_log.json");
const shakeIntensityFile = path.join(logsDir, "shake_intensity_log.json");
const recordingsFile = path.join(logsDir, "recordings_log.json");
const liveLocationsFile = path.join(logsDir, "live_locations_log.json");
const alertsFile = path.join(logsDir, "alerts_log.json");

// Helper function to save data to JSON file
function saveData(filename, data) {
  const existing = fs.existsSync(filename)
    ? JSON.parse(fs.readFileSync(filename, "utf8"))
    : [];
  existing.push(data);
  fs.writeFileSync(filename, JSON.stringify(existing, null, 2));
}

// Helper function to save shake intensity data
function saveShakeIntensity(filename, data) {
  const existing = fs.existsSync(filename)
    ? JSON.parse(fs.readFileSync(filename, "utf8"))
    : [];
  existing.push(data);
  // Keep only last 1000 entries
  if (existing.length > 1000) {
    existing.shift();
  }
  fs.writeFileSync(filename, JSON.stringify(existing, null, 2));
}

// Endpoint to receive shake intensity data
app.post("/shake-intensity", (req, res) => {
  const { intensity, acceleration, timestamp } = req.body;

  const shakeData = {
    intensity: intensity || "0",
    acceleration: acceleration || { x: "0", y: "0", z: "0" },
    timestamp: timestamp || new Date().toISOString(),
  };

  saveShakeIntensity(shakeIntensityFile, shakeData);
  res.json({ status: "Shake intensity logged successfully" });
});

// Endpoint to receive live location updates for an SOS
app.post("/sos-live", (req, res) => {
  const { sosId, latitude, longitude, timestamp } = req.body;
  const entry = {
    sosId: sosId || null,
    latitude: latitude || "Unknown",
    longitude: longitude || "Unknown",
    timestamp: timestamp || new Date().toISOString()
  };
  saveData(liveLocationsFile, entry);
  res.json({ status: 'Live location logged' });
});

// Endpoint to receive police alert requests
app.post("/alert-police", (req, res) => {
  const { sosId, location, details } = req.body;
  const entry = {
    sosId: sosId || null,
    location: location || {},
    details: details || {},
    timestamp: new Date().toISOString()
  };
  saveData(alertsFile, entry);
  console.log('🚓 Police alert logged', entry);
  res.json({ status: 'Police alert received' });
});

// Endpoint to broadcast to nearby users (placeholder logger)
app.post("/broadcast", (req, res) => {
  const { sosId, location, message } = req.body;
  const entry = {
    sosId: sosId || null,
    location: location || {},
    message: message || '',
    timestamp: new Date().toISOString()
  };
  saveData(alertsFile, entry);
  console.log('📣 Broadcast logged', entry);
  res.json({ status: 'Broadcast received' });
});

// Endpoint to mark a recording as locked (prevent deletion from logs)
app.post("/lock-recording", (req, res) => {
  const { filename, sosId } = req.body || {};
  if (!fs.existsSync(recordingsFile)) return res.status(404).json({ error: 'No recordings log' });
  const recordings = JSON.parse(fs.readFileSync(recordingsFile, 'utf8'));
  let updated = false;
  for (let r of recordings) {
    if ((filename && r.filename === filename) || (sosId && r.sosId == sosId)) {
      r.locked = true;
      updated = true;
    }
  }
  if (updated) {
    fs.writeFileSync(recordingsFile, JSON.stringify(recordings, null, 2));
    res.json({ status: 'Recording(s) locked' });
  } else {
    res.status(404).json({ error: 'Recording not found' });
  }
});

// Endpoint to receive SOS alerts
app.post("/sos", (req, res) => {
  const { user, time, intensity, location, userProfile, contactsNotified, triggeredBy } = req.body;

  const sosDetails = {
    user: user || "Anonymous",
    time: time || new Date().toISOString(),
    intensity: intensity || "N/A",
    location: location || "Unknown",
    userProfile: userProfile || {},
    contactsNotified: contactsNotified || 0,
    triggeredBy: triggeredBy || "Manual",
    recordingStarted: false
  };

  saveData(sosFile, sosDetails);
  console.log("🚨 SOS Logged:", sosDetails);

  res.json({ 
    status: "SOS data logged successfully",
    sosId: Date.now()
  });
});

// Endpoint to upload recorded video/photo
app.post("/upload-recording", upload.single("recording"), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No file uploaded" });
    }

    const recordingData = {
      filename: req.file.filename,
      originalName: req.file.originalname,
      size: req.file.size,
      mimetype: req.file.mimetype,
      uploadTime: new Date().toISOString(),
      sosId: req.body.sosId || null,
      user: req.body.user || "Anonymous",
      location: JSON.parse(req.body.location || '{}'),
      duration: req.body.duration || "Unknown"
    };

    saveData(recordingsFile, recordingData);
    console.log("📹 Recording uploaded:", recordingData.filename);

    res.json({ 
      status: "Recording uploaded successfully",
      fileUrl: `/uploads/${req.file.filename}`,
      recordingData
    });
  } catch (err) {
    console.error("Error uploading recording:", err);
    res.status(500).json({ error: "Failed to upload recording" });
  }
});

// Endpoint to get all recordings
app.get("/recordings", (req, res) => {
  if (!fs.existsSync(recordingsFile)) {
    return res.json([]);
  }
  const recordings = JSON.parse(fs.readFileSync(recordingsFile, "utf8"));
  res.json(recordings);
});

// Endpoint to download SOS logs
app.get("/download-sos", (req, res) => {
  if (!fs.existsSync(sosFile)) {
    return res.status(404).json({ error: "No SOS logs found" });
  }
  res.download(sosFile, "sos_log.json");
});

// Endpoint to download shake intensity logs
app.get("/download-shake-intensity", (req, res) => {
  if (!fs.existsSync(shakeIntensityFile)) {
    return res.status(404).json({ error: "No shake intensity logs found" });
  }
  res.download(shakeIntensityFile, "shake_intensity_log.json");
});

// Endpoint to download recordings log
app.get("/download-recordings", (req, res) => {
  if (!fs.existsSync(recordingsFile)) {
    return res.status(404).json({ error: "No recordings logs found" });
  }
  res.download(recordingsFile, "recordings_log.json");
});

// Endpoint to delete old files (cleanup)
app.delete("/cleanup/:days", (req, res) => {
  const days = parseInt(req.days) || 7;
  const cutoffTime = Date.now() - (days * 24 * 60 * 60 * 1000);
  
  try {
    const files = fs.readdirSync(uploadsDir);
    let deletedCount = 0;
    
    files.forEach(file => {
      const filePath = path.join(uploadsDir, file);
      const stats = fs.statSync(filePath);
      
      if (stats.mtimeMs < cutoffTime) {
        fs.unlinkSync(filePath);
        deletedCount++;
      }
    });
    
    res.json({ 
      status: "Cleanup completed",
      deletedFiles: deletedCount
    });
  } catch (err) {
    res.status(500).json({ error: "Cleanup failed" });
  }
});

app.listen(PORT, () => {
  console.log(`✅ Server running at http://localhost:${PORT}`);
  console.log(`📁 Uploads directory: ${uploadsDir}`);
  console.log(`📝 Logs directory: ${logsDir}`);
});
