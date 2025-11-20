halmoni is production ready music creative coding support library.

It should include functions that 
  - Analyze chord structure (chord, progression) from midi
  - Suggest chord progress substitute, restructure, split, merge on specific index.
  - Analyze chord play difficuly for each instrument. (Current target is 5 string guitar, piano, 4 string bass)


Our refernce library musicant has following classes
```
6385:Musicant.API.Definition
6386:Musicant.API.Subscription
6387:Musicant.API.Tunes.Types
6388:Musicant.API.Types
6389:Musicant.Core.ABC
6390:Musicant.Core.Accidental
6391:Musicant.Core.Bar
6392:Musicant.Core.Bar.MelodyLine
6393:Musicant.Core.Chord
6394:Musicant.Core.Chord.Voicing
6395:Musicant.Core.ChordInScale
6396:Musicant.Core.Degree
6397:Musicant.Core.Key
6398:Musicant.Core.KeyName
6399:Musicant.Core.NewInterval
6400:Musicant.Core.Note
6401:Musicant.Core.NoteInOctave
6402:Musicant.Core.NoteLength
6403:Musicant.Core.Octave
6404:Musicant.Core.Parser
6405:Musicant.Core.Progression.ABC
6406:Musicant.Core.Progression.ABCProgression
6407:Musicant.Core.Progression.ChordProgression
6408:Musicant.Core.Progression.Generator
6409:Musicant.Core.Scale
6410:Musicant.Core.Scale.Chords
6411:Musicant.Core.Suggestions.Compliments
6412:Musicant.Core.Suggestions.Revision.DoNotRepeatChords
6413:Musicant.Core.Suggestions.Revision.IdentifyNonDiatonicChords
6414:Musicant.Core.Suggestions.Revision.MoveUsingCommonNote
6415:Musicant.Core.Suggestions.Revision.ReviseNoteCompliments
6416:Musicant.Core.Suggestions.Revision.SmoothenBassMovement
6417:Musicant.Core.Suggestions.Strategy.BorrowedChord
6418:Musicant.Core.Suggestions.Strategy.ChromaticApproachChord
6419:Musicant.Core.Suggestions.Strategy.IsChordNote
6420:Musicant.Core.Suggestions.Strategy.NeapolitanChord
6421:Musicant.Core.Suggestions.Strategy.SubV7
6422:Musicant.Core.Suggestions.Strategy.Suspend
6423:Musicant.Core.Suggestions.Strategy.TSDMovementPattern
6424:Musicant.Core.Suggestions.Types
6425:Musicant.Core.TimeSignature
6426:Musicant.Defaults
6427:Musicant.Frontend.ProgressionInput
6428:Musicant.Tracking
6429:Musicant.Utilities
```

I want at least include all chord suggestion strategies.