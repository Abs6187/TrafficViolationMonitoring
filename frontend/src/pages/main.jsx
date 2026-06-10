import { useState } from "react";
import { useSetRecoilState } from "recoil";
import { fileState } from "../atoms/processedVideo";
import { useNavigate } from "react-router-dom";
// import { saveAs } from "file-saver";
const VideoPlayer = () => {
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [error, setError] = useState("");
  const setFile=useSetRecoilState(fileState);
 const navigate=useNavigate();
  const handleVideoChange = async (e) => {
    const nextFile = e.target.files[0];
    if (!nextFile) {
      setError("Please choose a video file.");
      return;
    }
    setError("");
    setFile(nextFile);
    setSelectedVideo(URL.createObjectURL(nextFile));
  };

  return (
    <div className="min-h-screen">
      <header className="pl-4 bg-slate-100 text-white shadow-lg flex justify-between items-center">
        <img src="../../public/images/logo.png" alt="" className="h-20 w-20" />
        <p className="text-red-600 text-2xl font-semibold font-sans">Traffic Violation Montioring</p>
        <div className="w-40">

        </div>
      </header>
      <main className=" min-w-full flex flex-col items-center justify-center mt-8">
        <label htmlFor="video-upload" className="w-4/6 h-[70vh] outline-dashed rounded-lg outline-red-600 flex items-center justify-center cursor-pointer shadow-lg">
          <div className="flex items-center flex-col text-xl text-red-600 font-sans">
            {!selectedVideo && (
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10">
                <path fillRule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm.53 5.47a.75.75 0 0 0-1.06 0l-3 3a.75.75 0 1 0 1.06 1.06l1.72-1.72v5.69a.75.75 0 0 0 1.5 0v-5.69l1.72 1.72a.75.75 0 1 0 1.06-1.06l-3-3Z" clipRule="evenodd" />
              </svg>
            )}

            {selectedVideo ? "" : "Click here to select a video"}
          </div>

          {selectedVideo && (
            <video controls src={selectedVideo} className="w-full rounded-lg" />
          )}
        </label>

        

        <input id="video-upload" type="file" accept="video/*" onChange={handleVideoChange} className="hidden" />
        <button className="bg-red-500 text-white px-4 py-2 rounded-md shadow hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50 mt-5" onClick={()=>{
          if (!selectedVideo) {
            setError("Select a video before continuing.");
            return;
          }
          navigate('/detect');
        }}>
      DETECT
    </button>
      {error && <div className="mt-3 rounded-md bg-red-100 px-4 py-3 text-red-700 shadow">{error}</div>}
      </main>
    </div>
  );
};

export default VideoPlayer;
