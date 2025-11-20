# Queue-able tasks

Below is list of remote procedure's description.

Task is long-time executing function so it's requests should be queued and result could be fetched by polling.
It has unified format of `/enqueue`,`/status`,`/result` endpoint.


Operations is short-time executing function. It's result is available immediately. Just like plain REST API call.


## Task : Audio seperation

Input : 
 - audio file (ffmpeg supported formats)
 - nesseary instrument separation

Output : 
 - separated audio files (.opus format)

Errors : 
 - if audio file is not supported
 - if no model is available for the instrument

## Task : Audio transcription

Input : 
 - audio file (ffmpeg supported formats)
 - instrument name

Output : 
 - transcription file (.mid format)

Errors : 
 - if audio file is not supported
 - if no model is available for the instrument

## Task : Chord recognition

Input : 
 - transcription file (.mid format)

Output : 
 - chord recognition file (.txt,.json format)

Errors : 
 - if transcription file is not supported
 - if input midi has unknown chords or measure

## Task : Audio chord reharmonization

Might use LLM.

Input : 
 - transcription file (.mid format)
 - reharmonization rules

Output : 
 - reharmonized transcription file (.mid format)

Errors : 
 - if transcription file is not supported

## Task : E2E base ready for reharmonization

Is step function that combines all the tasks (seperation, transcription, chord recognition) above.

Input : 
 - base audio file (ffmpeg supported formats)
 - instrument name

Output : 
 - transcription file (.mid format)
 - separated audio (.opus format)
 - chord progression file (.txt,.json format)

Errors : 
 - if base audio file is not supported
 - if instrument name is not supported
 
## Task : Easier chord recommandateion

Input : 
 - chord progression file (.txt,.json format)
 - target instrument name

Output : 
 - easier chord progression file (.txt,.json format)

Errors : 
 - if chord progression file is not supported
 - if target instrument name is not supported

## Operation : Alternative chord recommendation

Input : 
 - chord progression file (.txt,.json format)
 - index of the chord to substitute

Output : 
 - alternative chord recommendation file (.mid format)

Errors : 
 - if transcription file is not supported


## Operation : Calculate score's difficulty

Input : 
 - chord progression file (.json format)

Output : 
 - 