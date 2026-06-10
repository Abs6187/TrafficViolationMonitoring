import {BrowserRouter,Routes,Route} from 'react-router-dom'
import VideoPlayer from './pages/main'
import { Detect } from './pages/detect'
import { RecoilRoot } from 'recoil'
import Numberplate from './pages/forNumberPlate'
import { Image } from './pages/image'
function App() {

  return <>
  <BrowserRouter>
    <RecoilRoot>
  <Routes>

  <Route path='/' element={<VideoPlayer></VideoPlayer>}></Route>
  <Route path='/detect' element={<Detect></Detect>}></Route>
  <Route path='/numberplate' element={<Numberplate></Numberplate>}></Route>
  <Route path='/image' element={<Image></Image>}></Route>
  </Routes>
    </RecoilRoot>
  </BrowserRouter>
  </>
}

export default App
