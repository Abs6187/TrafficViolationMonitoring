import { useRecoilState, useRecoilValue } from "recoil";
import { fileState, processedVideoState } from "../atoms/processedVideo";
import { useState, useEffect } from "react";
import axios from "axios";
import { apiUrl } from "../lib/api";

// Helper: decode a real error message from an arraybuffer response.
// When axios uses responseType:"arraybuffer", even 4xx/5xx bodies arrive as
// binary. We decode them here so we can show the actual server error string.
function extractErrorMessage(err) {
  try {
    const data = err?.response?.data;
    if (!data) return null;

    // Already a plain object (non-arraybuffer path)
    if (typeof data === "object" && !(data instanceof ArrayBuffer) && !ArrayBuffer.isView(data)) {
      return data.error || data.message || null;
    }

    // ArrayBuffer or Uint8Array — decode as UTF-8 JSON
    const buf = data instanceof ArrayBuffer ? data : data.buffer;
    const text = new TextDecoder("utf-8").decode(buf);
    const parsed = JSON.parse(text);
    return parsed.error || parsed.message || text;
  } catch {
    return null;
  }
}

export function Detect() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [serverDetail, setServerDetail] = useState(""); // real server message
  const file = useRecoilValue(fileState);
  const [processedVideo, setProcessedVideo] = useRecoilState(processedVideoState);

  useEffect(() => {
    const detectTrafficViolation = async () => {
      if (!file) {
        setError("Please choose a video before starting detection.");
        return;
      }

      try {
        setLoading(true);
        setError("");
        setServerDetail("");

        const formData = new FormData();
        formData.append("video", file);

        const response = await axios.post(apiUrl("/detect/video"), formData, {
          headers: { "Content-Type": "multipart/form-data" },
          // Use arraybuffer so we receive the binary video on success.
          // Error messages are decoded manually via extractErrorMessage().
          responseType: "arraybuffer",
          // 10-minute timeout — video processing can be slow on CPU
          timeout: 600_000,
        });

        // Check for a JSON error body wrapped in a 200 (shouldn't happen, but guard it)
        const contentType = response.headers["content-type"] || "";
        if (contentType.includes("application/json")) {
          const text = new TextDecoder("utf-8").decode(response.data);
          const parsed = JSON.parse(text);
          if (parsed.error) throw new Error(parsed.error);
        }

        const videoBlob = new Blob([response.data], { type: "video/mp4" });
        setProcessedVideo(URL.createObjectURL(videoBlob));
      } catch (err) {
        console.error("Video detection error:", err);

        // Try to get the real message from the arraybuffer error body
        const serverMsg = extractErrorMessage(err);
        const status = err?.response?.status;

        if (status === 503) {
          setError("Model not ready — the server could not find the YOLO weights.");
          setServerDetail(serverMsg || "");
        } else if (status === 400) {
          setError("Bad request: " + (serverMsg || "invalid video file"));
        } else if (err.code === "ECONNABORTED" || err.message?.includes("timeout")) {
          setError("Request timed out. The video may be too long — try a shorter clip.");
        } else if (!err.response) {
          setError("Cannot reach the backend. Make sure the Flask server is running on port 5000.");
        } else {
          setError(serverMsg || "Video detection failed. Check the browser console for details.");
          setServerDetail(serverMsg ? "" : String(err));
        }
      } finally {
        setLoading(false);
      }
    };

    detectTrafficViolation();
  }, [file, setProcessedVideo]);

  if (loading) {
    return (
      <div className="min-h-screen min-w-screen flex flex-col gap-4 justify-center items-center">
        <div role="status">
          <svg
            aria-hidden="true"
            className="inline w-20 h-20 text-gray-200 animate-spin dark:text-gray-600 fill-red-600"
            viewBox="0 0 100 101"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
              fill="currentColor"
            />
            <path
              d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
              fill="currentFill"
            />
          </svg>
          <span className="sr-only">Processing video...</span>
        </div>
        <p className="text-gray-500 text-sm">Processing video — this may take a minute on CPU…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen min-w-screen flex flex-col justify-center items-center gap-4">
      {processedVideo && (
        <video controls src={processedVideo} className="w-4/6 h-[70vh] rounded-lg shadow-lg" />
      )}
      {!processedVideo && error && (
        <div className="w-4/6 rounded-md bg-red-100 px-4 py-3 text-red-700 shadow">
          <p className="font-semibold">{error}</p>
          {serverDetail && (
            <p className="mt-1 text-xs font-mono text-red-500 break-all">{serverDetail}</p>
          )}
        </div>
      )}
    </div>
  );
}
