# Project description
Project for 2026 IFG fashion show DJ sessions


Feature list:
1. Create/extend to 30 mins long backtracks for selected audio files
2. An interface to specify remix specifications for creating each 30-min long track
   2-1. Start/end timer indicator to specify the portion of sound file to use to remix 30 minutes long sessions
3. (optional) a program to play the DJ list with simple interface


## Project layout

```
├── audios/              # source MP3 files
├── configs/             # remix YAML configs
├── outputs/             # generated mixes
├── scripts/
│   └── audio_re-mixer.py
└── requirements.txt
```

Paths in YAML (`source_file`, `output_file`) are relative to the project root.


## Commands

Run from the project root:

```bash
pip install -r requirements.txt

python3 scripts/audio_re-mixer.py configs/the_mission.yaml
python3 scripts/audio_re-mixer.py configs/a_thousand_years.yaml
```

Shorthand (config name only, resolved from `configs/`):

```bash
python3 scripts/audio_re-mixer.py the_mission.yaml
```
