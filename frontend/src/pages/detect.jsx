import { useRecoilState, useRecoilValue } from "recoil"
import { fileState, processedVideoState } from "../atoms/processedVideo"
import { useState } from "react";
import { useEffect } from "react";
import axios from "axios";
import { apiUrl } from "../lib/api";
export function Detect(){
    const [loading,setLoading]=useState(false);
    const [error, setError] = useState("");
    const file=useRecoilValue(fileState);
    const [processedVideo,setProcessedVideo] = useRecoilState(processedVideoState);
    useEffect(()=>{
        const detectTrafficViolation = async () => {
            if (!file) {
              setError("Please choose a video before starting detection.");
              return;
            }

            try {
              setLoading(true); // Set loading to true while video is being processed
              setError("");
      
              // Make the request to predict traffic violations
              const formData = new FormData();
              formData.append("video", file);
      
              const response = await axios.post(apiUrl("/detect/video"), formData, {
                headers: {
                  "Content-Type": "multipart/form-data"
                },
                responseType: "arraybuffer"
              });
      
              // Process the response and set the processed video
              const videoBlob = new Blob([response.data], { type: 'video/mp4' });
              const url = URL.createObjectURL(videoBlob);
              setProcessedVideo(url);
            } catch (error) {
              console.error("Error sending video to backend:", error);
              setError(error?.response?.data?.error || "Video detection failed. Please verify the model is configured.");
            } finally {
              setLoading(false); // Set loading to false when video processing is complete
            }
          };
      
          detectTrafficViolation();
    },[file, setProcessedVideo]);
    if(loading){
        return <div className="min-h-screen min-w-screen flex justify-center items-center">
<div role="status">
    <svg aria-hidden="true" className="inline w-20 h-20 text-gray-200 animate-spin dark:text-gray-600 fill-red-600" viewBox="0 0 100 101" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z" fill="currentColor"/>
        <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z" fill="currentFill"/>
    </svg>
    <span className="sr-only">Loading...</span>
</div>
        </div>
    }
    return <div className="min-h-screen min-w-screen flex justify-center items-center">
        {processedVideo && (
          <video controls src={processedVideo} className="w-4/6 h-[70vh] rounded-lg" />
        )}
        {!processedVideo && error && (
          <div className="rounded-md bg-red-100 px-4 py-3 text-red-700 shadow">{error}</div>
        )}

    </div>
}
