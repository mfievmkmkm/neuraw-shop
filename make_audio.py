"""Generate an original, instrumental portfolio sketch (not a finished song)."""
import numpy as np
import wave
from pathlib import Path
sr=44100
length=16
out=np.zeros(sr*length,dtype=np.float64)
notes={'C4':261.63,'D4':293.66,'E4':329.63,'G4':392.0,'A4':440.0,'C5':523.25,'D5':587.33,'E5':659.25,'G3':196.0,'A3':220.0,'F3':174.61}
def tone(freq,dur,amp=.2):
 t=np.arange(int(sr*dur))/sr
 e=np.minimum(1,t/.03)*np.minimum(1,(dur-t)/.3)
 return amp*e*(np.sin(2*np.pi*freq*t)+.20*np.sin(2*np.pi*2*freq*t)+.08*np.sin(2*np.pi*3*freq*t))
def put(start,name,dur,amp):
 s=int(start*sr); v=tone(notes[name],dur,amp);out[s:s+len(v)]+=v
for bar,chord in enumerate([('A3','C4','E4'),('F3','A3','C4'),('G3','D4','G4'),('A3','C4','E4')]):
 for note in chord:put(bar*4,note,3.8,.055)
melody=['E5','D5','C5','E5','G4','A4','C5','D5','E5','C5','A4','G4','C5','D5','E5','C5']
for i,n in enumerate(melody):put(i,n,.82,.13)
for beat in np.arange(0,16,.5):
 s=int(beat*sr);t=np.arange(4000)/sr
 kick=.08*np.exp(-24*t)*np.sin(2*np.pi*(95-55*t)*t)
 out[s:s+len(kick)]+=kick
out=np.tanh(out*1.4)
p=Path(__file__).parent/'assets'/'music-sketch.wav'
with wave.open(str(p),'wb') as w:
 w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((out*32767).astype('<i2').tobytes())
