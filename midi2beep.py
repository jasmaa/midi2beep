import mido
import audiolazy
import sys

def count_cols(track):
    """Count max columns needed for a track"""
    max_count = -1
    count = 0
    for m in track:
        if m.type == "note_on":
            count += 1
        elif m.type == "note_off":
            count -= 1

        max_count = max(max_count, count)
    return max_count

def pad_streams(streams, total_time):
    """Pad to current time"""
    for s in streams:
        while len(s) < total_time+1:
            s.append(s[-1])

# === MAIN ===
if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: midi2beep.py <midi file>")
        exit(1)
    
    m = mido.MidiFile(sys.argv[1])

    tempo = 500000
    all_streams = []

    # process tracks
    for track in m.tracks:
        print("Track: " + track.name)
        glob_time = 0
        streams = []
        n_cols = count_cols(track)
        for i in range(n_cols):
            streams.append([-1])

        print("#Cols: " + str(n_cols))

        for msg in track:
            
            if msg.type == "set_tempo":
                tempo = msg.tempo
            
            # process notes
            if not msg.is_meta:
                if msg.type == "note_on":
                    set_flag = False
                    glob_time += msg.time
                    pad_streams(streams, glob_time)
                    # find position to start note
                    for s in streams:
                        if not set_flag and s[-1] == -1:
                            s[-1] = msg.note
                            set_flag = True
                    
                elif msg.type == "note_off":
                    set_flag = False
                    glob_time += msg.time
                    pad_streams(streams, glob_time)
                    # locate and stop note
                    for s in streams:
                        if not set_flag and s[-1] == msg.note:
                            s[-1] = -1
                            set_flag = True

        all_streams += streams

    # naive highest note extraction
    single_stream = []
    min_len = 999999999999999999999999999
    for s in all_streams:
        min_len = min(min_len, len(s))

    for i in range(min_len):
        max_note = -1
        for s in all_streams:
            max_note = max(max_note, s[i])
        single_stream.append(max_note)

    # convert single stream to commands
    cmds = [(-1, 0)]
    counter = 0
    curr_note = -1
    for n in single_stream:
        if curr_note != n:
            cmds.append((
                -1 if curr_note == -1 else int(audiolazy.midi2freq(curr_note)),
                int(mido.tick2second(counter, m.ticks_per_beat, tempo) * 500)
            ))
            curr_note = n
            counter = 0
        else:
            counter += 1

    print("Command head: " + str(cmds[:10]))
    print("Done!")

    # write out
    with open("out.py", "w") as f:
        f.write("import winsound, time\n\n")
        for c in cmds:
            if c[0] == -1:
                f.write(f"time.sleep({c[1]} / 1000.0)\n")
            else:
                f.write(f"winsound.Beep({c[0]}, {c[1]})\n")

    with open("out.txt", "w") as f:
        for c in cmds:
            if c[0] == -1:
                f.write(f"delay({c[1]});\n")
            else:
                f.write(f"CircuitPlayground.playTone({c[0]}, {c[1]});\n")
            
