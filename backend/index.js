const express = require("express");
const { User } = require("./db");
const cors = require("cors");
const axios = require("axios");
const multer = require("multer");
const FormData = require("form-data");
const fs = require("fs");
const path = require("path");
const app = express();
app.use(express.json());
app.use(cors());

const PORT = Number(process.env.PORT || 3000);
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || "http://127.0.0.1:5000/api";
const TWILIO_ACCOUNT_SID = process.env.TWILIO_ACCOUNT_SID || "";
const TWILIO_AUTH_TOKEN = process.env.TWILIO_AUTH_TOKEN || "";
const TWILIO_FROM_NUMBER = process.env.TWILIO_FROM_NUMBER || "";
const DEFAULT_NOTIFICATION_TO = process.env.DEFAULT_NOTIFICATION_TO || "";

const uploadsDir = path.join(__dirname, "uploads");
fs.mkdirSync(uploadsDir, { recursive: true });

const storage = multer.diskStorage({
    destination: function (req, file, cb) {
      cb(null, uploadsDir);
    },
    filename: function (req, file, cb) {
      cb(null, file.originalname); // Keep the original filename
    }
});
const client = TWILIO_ACCOUNT_SID && TWILIO_AUTH_TOKEN
  ? require("twilio")(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
  : null;
  
const upload = multer({ storage: storage });
app.post('/addNumberPlate',async (req,res)=>{
    try {
        const numberplateDetails=req.body;
        if (!numberplateDetails?.numberplate) {
            return res.status(400).json({ error: "numberplate is required" });
        }

        const user=(await User.find({ numberplate: numberplateDetails.numberplate })).length;
        if(!user){
            const plate=new User(numberplateDetails);
            await plate.save();

            let smsStatus = "notification skipped";
            if (client && TWILIO_FROM_NUMBER && (numberplateDetails.phonenumber || DEFAULT_NOTIFICATION_TO)) {
                const message = await client.messages.create({
                    body: `Traffic violation detected for ${numberplateDetails.numberplate}.`,
                    from: TWILIO_FROM_NUMBER,
                    to: numberplateDetails.phonenumber || DEFAULT_NOTIFICATION_TO
                });
                smsStatus = `message sent successfully (${message.sid})`;
            }

            return res.json({ status: 'success', msg: smsStatus ,r:1});
        }

        return res.json({
            msg:"Already exists",
            r:0
        });
    } catch (error) {
        console.error(error);
        return res.status(500).json({ error: error.message });
    }
})
app.post('/predict', upload.single('video'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No video file provided' });
        }
        
        const form = new FormData();
        // console.log(req.file.path)
        form.append('video', fs.createReadStream(req.file.path));
        // console.log(form.getHeaders())
        // console.log(form)
        const response = await axios.post(`${ML_SERVICE_URL}/detect/video`, form, {
            headers: {
                ...form.getHeaders()
            },
            responseType: "stream",
            timeout: 300000,
        });
        console.log("RESPONSE");
        // console.log(response);
        response.data.pipe(res);
    } catch (error) {
        console.error("Error predicting:", error);
        res.status(500).json({ error: error.toString() });
    } finally {
        if (req.file?.path) {
            fs.unlink(req.file.path, () => {});
        }
    }
});

app.get("/health", (_req, res) => {
    res.json({ status: "ok", mlServiceUrl: ML_SERVICE_URL });
});

  
app.listen(PORT, () => console.log(`Server running on port ${PORT}`))
