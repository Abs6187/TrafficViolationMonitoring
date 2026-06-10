import { atom } from 'recoil';
export const processedVideoState = atom({
  key: 'processedVideoState', // Unique ID for this atom
  default: null, // Initial value of the atom
});
export const processedImageState = atom({
  key: 'processedImageState', // Unique ID for this atom
  default: null, // Initial value of the atom
});
export const fileState=atom({
    key:'file',
    default:null
})
export const imageState=atom({
  key:'img',
  default:null
})
