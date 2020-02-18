import mido
import numpy as np
from Node import Node
from scipy.io import wavfile as wav
from scipy import signal
import tkinter as tk


def get_frequency(d):
    """
    Ger frekvensen för en viss not d
    :param d: Notnummer
    :return: Frekvensen
    """
    return 440 * 2**((d-69)/12)


def tone_generator(msg, duration, sample_frequency):
    """
    Ger en ton(sinusvåg) från en not
    :param msg: info från midifilen om noten
    :param duration: hur länge noten spelas
    :param sample_frequency: Samplefrekvensen
    :return: Vektor med tonen
    """
    time = np.linspace(0, duration, sample_frequency*duration)
    frequency = get_frequency(msg.note)
    tone = np.sin(2*np.pi*frequency*time)*msg.velocity
    # Övertoner
    tone += (np.sin(2 * np.pi * frequency * time * 2) * msg.velocity) * 0.6
    tone += (np.sin(2 * np.pi * frequency * time * 3) * msg.velocity) * 0.5
    tone += (np.sin(2 * np.pi * frequency * time * 4) * msg.velocity) * 0.4
    tone += (np.sin(2 * np.pi * frequency * time * 5) * msg.velocity) * 0.3
    tone += (np.sin(2 * np.pi * frequency * time * 6) * msg.velocity) * 0.2
    return tone


def generate_sound(mid_file, sample_frequency, number_of_tracks):
    """
    Omvandlar en midi fil till ljud i form av en sinusvåg
    :param mid_file: midi-filen
    :param sample_frequency:  Samplefrekvensen
    :return: Vektor som innehåller ljudet
    """
    midi_total_time = mid_file.length
    sound = np.zeros(int(sample_frequency*midi_total_time))
    tempo = 500000  # Standardtempo
    # Plockar ut varje track som är ett typ av ljud
    for i, track in enumerate(mid_file.tracks):
        found_notes = {}
        total_time = 0
        # Varje message som är en ton
        if i < number_of_tracks:
            for msg in track:
                total_time += mido.tick2second(msg.time, mid_file.ticks_per_beat, tempo)
                if msg.type == 'set_tempo':
                    tempo = msg.tempo
                elif msg.type == 'note_on':
                    if msg.note not in found_notes:
                        found_notes[msg.note] = Node(msg, total_time)
                    else:
                        msg_first = found_notes.pop(msg.note)
                        duration = total_time - msg_first.time
                        tone = tone_generator(msg_first.data, duration, sample_frequency)
                        sound[int(msg_first.time*sample_frequency):int(msg_first.time*sample_frequency)+int(duration*sample_frequency)] += tone
                elif msg.type == 'note_off':
                    if msg.note not in found_notes:
                        continue
                    msg_first = found_notes.pop(msg.note)
                    duration = total_time - msg_first.time
                    tone = tone_generator(msg_first.data, duration, sample_frequency)
                    sound[int(msg_first.time * sample_frequency):int(msg_first.time * sample_frequency) + int(
                        duration * sample_frequency)] += tone
    sound = sound*0.001
    sound = np.clip(sound, -0.95, 0.95)
    return sound


def get_song(song, filter):
    mid = ""
    number_of_tracks = ""
    new_filename = ""
    if song == "I Want It That Way - Backstreet Boys":
        mid = mido.MidiFile('backstreet.mid')
        number_of_tracks = 17
        new_filename = "i_want_it_that_way.wav"
    elif song == "Sweet Child O' Mine - Guns N' Roses":
        mid = mido.MidiFile('guns.mid')
        number_of_tracks = 16
        new_filename = "sweet_child_o_mine.wav"
    elif song == "Pirates of the Caribbean":
        mid = mido.MidiFile('pirate.mid')
        number_of_tracks = 3
        new_filename = "pirates_of_the_caribbean.wav"
    elif song == "All Star - Smash Mouth":
        mid = mido.MidiFile('allstar.mid')
        number_of_tracks = 6
        new_filename = "all_star.wav"

    sample_frequency = 44100
    print("Genererar ljudfilen..")
    y = generate_sound(mid, sample_frequency, number_of_tracks)
    if filter != "Inget":
        y = apply_filter(filter, y)
    wav.write(new_filename, sample_frequency, y)
    print("Din låt finns nu att lyssna på med namnet " + new_filename + "!")


def apply_filter(filter, y):
    if filter == "Lågpass":
        b_lp = ideal_lowpass()
        return fir_filter(b_lp, y)
        print("lågpass")
    elif filter == "Högpass":
        b_hp = ideal_highpass()
        return fir_filter(b_hp, y) * 100


def fir_filter(B, X):
    Y = np.zeros(X.shape)
    for index in range(len(X)):
        sum = 0
        for koeff in range(len(B)):
            if index-koeff < 0:
                sum += 0
            else:
                sum += B[koeff]*X[index-koeff]
        Y[index] = sum
    return Y


def ideal_lowpass(f=0.01):
    n = 60
    x = np.arange(0, n)-(n-1)/2  # create time axis n from -(N-1)/2 to (N-1)/2
    b = np.sinc(f*x)           # evaluate sinc function
                             # with freq F for all n
    b *= signal.hamming(n)     # multiply by hamming window
                             # to soften truncation
    b /= np.sum(b)             # make total sum 1 (= unit gain at zero frequency)
    return b


def ideal_highpass():
    f = 0.85  # Brytfrekvens
    n = 60
    blp = ideal_lowpass(f)        # get low-pass coefficients
                             # now create an impulse centered at (N-1)/2:
    bhp = np.zeros(n)          # step 1: zero vector
    if n % 2:                    # step 2 a (if N is odd):
        bhp[int((n-1)/2)] = 1      #  set element at (N-1)/2 to one
    else:                      # step 2 b (if N is even):
        bhp[int((n-1)/2)] = 0.5    #  set elements at (N-1)/2 and (N-1)/2+1 to 0.5
        bhp[int((n-1)/2+1)] = 0.5
    bhp = bhp - blp            # step 3: get the high-pass coefficients
                             #  by subtracting low-pass from impulse
    return bhp


def main():
    root = tk.Tk()
    root.title("Spela upp Midi-fil")

    # Skapa grid
    mainframe = tk.Frame(root)

    mainframe.grid()

    # Välja midi-fil
    tk.Label(mainframe, text="Välj en midi-fil att läsa in:").grid(row=0, column=0)
    song = tk.StringVar(root)
    song_choices = {"I Want It That Way - Backstreet Boys", "Sweet Child O' Mine - Guns N' Roses", "Pirates of the Caribbean", "All Star - Smash Mouth"}
    song.set("I Want It That Way - Backstreet Boys")
    dropdown = tk.OptionMenu(mainframe, song, *song_choices)
    dropdown.grid(row=0, column=1)

    # Välja filter
    tk.Label(mainframe, text="Filter:").grid(row=1, column=0)
    filter = tk.StringVar()
    filter.set("Inget")
    rb1 = tk.Radiobutton(mainframe, text="Inget", variable=filter, value="Inget")
    rb2 = tk.Radiobutton(mainframe, text="Högpass", variable=filter, value="Högpass")
    rb3 = tk.Radiobutton(mainframe, text="Lågpass", variable=filter, value="Lågpass")
    rb1.grid(row=1, column=1)
    rb2.grid(row=2, column=1)
    rb3.grid(row=3, column=1)

    # Knapp för att spara ljud
    tk.Button(mainframe, text="Spela Ljud", command=lambda: get_song(song.get(), filter.get())).grid(row=4, column=0)
    root.mainloop()


if __name__ == "__main__":
    main()


