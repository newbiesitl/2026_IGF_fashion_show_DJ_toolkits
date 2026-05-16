"""
Goal:
To create a X minutes long audio track

Input configuration yaml




For example:
apashe.mp3
source_file: audios/the_mission.mp3
session_configs:
- start: 0
  end : 153
  fade_in : 200
  fade_out : 500
- start: 5
  end : 147
  fade_in : 200
  fade_out : 500
- start: 8
  end : 140
  fade_in : 200
  fade_out : 500



It means the program reads the audio file apashe.mp3, let's say the file is 153 seconds long
In each item in session_configs it describes the start and end time stamp of each session used to remix the long audio track
first item means extract the audio file from 0 sec to 153 sec and add it to the remix as the first section, with fade in set to 200ms, and fade out set to 500ms
second item means extract the audio file from 5 sec to 147 sec and add it to the remix as the second section, with fade in set to 200ms, and fade out set to 500ms
third item means extract the audio file from 8 sec to 140 sec and add it to the remix as the third section, with fade in set to 200ms, and fade out set to 500ms
so in total , the program mixes 3 sections of audios into one and the total length of the audio file is
(153 - 0) + (147 - 5) + (140 - 8)

"""