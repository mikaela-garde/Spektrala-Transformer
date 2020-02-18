# -*- coding: utf-8 -*-
"""LAB_C_HT19-1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Ep_6LHn7WNrub1lvvpLdSxG-YnLjRbzP

# DT1130 LAB C - JPEG-kodning

I denna laboration kommer du att få experimentera med transfom-baserad bildkompression enligt JPEG-metoden. Du kommer att implementera en förenklad form av JPEG-kodare/avkodare för gråskalebilder, och pröva olika strategier för att ta bort redundant information i bilden, uppskatta kompressionsgrad och ställa denna i relation till upplevd bildkvalitet.

### Hjälp och redovisning
För att få hjälp under labpasset, använd [Queue-systemet](http://queue.csc.kth.se/#/queue/DT1130) för att tillkalla Labassistent. För att få hjälp övrig tid, skriv ett inlägg under [Hjälp på Canvas](
  https://kth.instructure.com/courses/12513/discussion_topics/84209
  ).

När du är klar med labben behöver du göra två saker:
* Redovisa för en labassistent under ett labpass (använd [Queue-systemet](http://queue.csc.kth.se/#/queue/DT1130) för att meddela att du är klar att redovisa)
* Lämna in din lab som **.ipynb**-fil i Canvas (Ladda ner från Colab med **File | Download .ipynb**)

## Innan vi börjar
Det första man ska göra är att spara en egen kopia av detta labbpek då detta är skrivskyddat. Detta gör man antingen genom att klicka på open in playground eller *File* -> *Save a copy in drive*.

### Ladda in lite data

Hämta paketet med [labdata](https://www.dropbox.com/s/zwhbijy9k8t8u5x/labdata.zip?dl=1) om du inte redan gjort det. Det innehåller ljudfiler som du kan använda för att testa dina filter. Ladda in dem i Colab (Se [jobba med filer](https://colab.research.google.com/drive/1LoIS5JzeupGVf6a4-A0sBxAeOnxzdXW8?authuser=1#scrollTo=bmTBuKQMRoa_) i labintroduktionen)

### Ladda bibliotek

Slutligen behöver vi importera ett antal bibliotek som kommer ska användas under labben. Kör koden nedan för att göra det!
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import imageio
import math

"""##JPEG-komprimering

JPEG-metoden för bildkomprimering är en transformbaserad kompressionsmetod. Det innebär att bilden transformeras med en spektral transform för att informationen ska kunna packas effektivare. Det är en approximativ metod, där information går förlorad i processen (s.k. lossy compression). Transformen som används i JPEG heter DCT\*, Discrete Cosine Transform och är en nära släkting till DFT, den diskreta fouriertransformen. DCT’n skiljer sig från DFT’n genom att endast använda cosinus-funktioner som basvektorer. DCT:n är en helt reell transform, dvs basfunktionerna är reella, och därmed också invektor och utvektor.

Det första som görs när en bild ska JPEG-kodas är att dela upp bilden i block av $8\times 8$ pixlars storlek. Detta görs huvudsakligen av effektivitetsskäl. Att göra DCT på hela bilden skulle ta alldeles för lång tid, även om större block principiellt leder till högre möjlig kompressionsgrad.

Därefter transformeras varje block med DCT i två dimensioner. Det transformerade blocket, en matris med $8\times 8$  koefficinter, beskriver blockets frekvensinnehåll. Första koefficienten $(1,1)$ motsvarar blockets genomsnittliga intensitet. Det visar sig att den mesta informationen finns i övre vänstra hörnet, som motsvarar låga spatiala frekvenser. Ju längre mot högra nedre hörnet man kommer, desto lägre belopp har koefficienterna och många är i praktiken noll. Därför kan dessa koefficienter elimineras eller kodas med färre bitar (kvantiseras) utan att bilden försämras lika mycket.

Efter att koefficienterna har kvantiserats kommer en stor del av dessa att vara noll, och kan därför packas ihop mycket effektivt med “traditionella” datakompressionsmetoder, bl.a. Huffman- kodning. (Detta steg hoppar vi över i denna laboration, vi nöjer oss med att räkna andelen koefficenter skiljda från noll och tar detta som ett grovt mått på kompressionsgraden.)

Avkodningen tillbaks till en bild sker därefter på omvänt sätt: koefficientmatriserna transformeras tillbaka till $8\times 8$-bilder, vilka tillsammans bildar den avkodade bilden. För mer information om JPEG-komprimering, läs kapitel 27 i gratisboken av Stephen W. Smith (se länk från kurshemsidan).

\* Detta gäller den ursprungliga JPEG-metoden. I en uppdaterad standard kallad JPEG2000 används istället en s.k. Wavelet-transform.

## DCT

DCT är kärnan i JPEG-algoritmen. DCT-transformen kan beräknas effektivt med en metod som liknar FFT, men för korta sekvenslängder, t.ex. 8 som är aktuellt här, är ändå det snabbaste sättet att beräkna den direkt genom en matrismultiplikation med en basvektormatris $T$. Denna $M \times M$-matris, där kolumnerna motsvarar DCT:ns basvektorer, beskrivs av
$$t_{pq} = \begin{cases} \frac{1}{\sqrt{M}} & 0\leq p \leq M, q=0\\
\sqrt{\frac{2}{M}}\cos \frac{\pi (2p+1)q}{2M} & 0\leq p\leq M-1, 1\leq q\leq M-1
\end{cases}$$
där $t_{pq}$ betecknar elementet på rad $p$, kolumn $q$.

Givet en radvektor $X$ av längd $M$ ges DCT:n av matrisprodukten $Y = XT$. Om $X$ är en matris så transformeras varje rad i matrisen.

För att transformera en bild $I$ i två dimensioner, så ska först raderna transformeras, sedan kolumnerna (eller vice-versa). Givet att $I$ är en $M\times M$-matris (dvs samma storlek som bas- vektormatrisen) så motsvarar detta $C=(((IT)^T)T)^T$ vilket kan förenklas till följande kompakta uttryck för 2D DCT:n av matrisen $I$:
$$C=T^T IT,$$
där $T^T$ betecknar matrisen $T$:s transponat.

Den inversa transformen, d.v.s. att återgå till $X$ från DCT-koefficienter, innebär helt enkelt att multiplicera med basvektormatrisen $T$:s invers. Nu är dock $T$ så beskaffad att inversen $T^{−1}$ är lika medtransponatet $T^T$ (detta förhållande gäller alla ortogonala matriser, d.v.s. matriser där kolumnernas inbördes skalärprodukter alla är noll), vilket innebär att inversen av transformen $Y =XT$ ges av $X=YT^T$. I det tvådimensionella fallet, där det gäller att återfå “bilden” $I$ från koefficientmatrisen $C$ ges av
$$I = TCT^T.$$

## Matrismultiplikation och transponat i Numpy

Matrismultiplikation mellan två np-arrayer `A` och `B` görs med `A @ B` eller `np.matmul(A,B)`

Transponatet av `A` ges av `A.T`
"""

# exempel på transponat och matrismultplikation

A = np.array([[1,2,3]])
B = A.T
C = A@B
D = B@A

print('A.shape: ',A.shape)
print('A:\n',A)
print('B.shape: ',B.shape)
print('B:\n',B)
print('C.shape: ',C.shape)
print('C:\n',C)
print('D.shape: ',D.shape)
print('D:\n',D)

"""## Uppgift 1

Skriv funktionen `dct_basis()` som beräknar DCT:ns basvektormatris av ordningen $m$.
"""

# Function: dct_basis for calculating dct-base-vector matrix
# Input: m (positive integer) - Basis vector length
# Output: T (mxm matrix) - DCT basis matrix, each column: basis vector
def dct_basis(m):
  # Initialize a matrix 
  T = np.zeros((m, m))
  for p in range(T.shape[0]):
    for q in range(T.shape[1]):
      if q == 0:
        T[p,q] = 1/np.sqrt(m)
      else:
        T[p,q] = np.sqrt(2/m)*np.cos((np.pi*(2*p + 1)*q)/(2*m))
  return T

"""### Testa din DCT!

För att testa att basvektormatrisen är korrekt kan du transformera några speciella $8\times 8$-matriser:
*  en matris med bara ettor - ska resultera i en koefficientmatris där  elementet i övre vänstra hörnet är åtta (8) (detta element motsvarar konstant-nivån) och övriga element nästan noll.
*   en matris där varannan kolumn är 1 och varannan kolumn −1 - ska resultera i en koefficientmatris där största elementet finns i övre högra hörnet.
*   enhetsmatrisen `np.identity(8)` - ska resultera i en enhetsmatris!


Visualisera resultatet med hjälp av `plt.subplot()` och `plt.imshow()`. Imshow ger automatiskt ett rutnät vilket kan vara störande när man visualiserar matriser - det kan stängas av genom att anropa `plt.grid(False)` innan imshow. 

*Att redovisa: Python-kod*
"""

# TEST ONES
X = np.ones((8,8))
T = dct_basis(8)
Y = T.T@X@T
plt.subplot(1,3,1)
plt.imshow(Y)
plt.title("ONES")

# TEST VARANNAN
X = np.ones((8,8))
for i in range(X.shape[0]):
  for j in range(X.shape[1]):
    if j % 2 == 1:
      X[i, j] = -1
Y = T.T@X@T
plt.subplot(1,3,2)
plt.imshow(Y)
plt.title("VARANNAN")

# TEST IDENTITY
X = np.identity(8)
Y = T.T@X@T
plt.subplot(1,3,3)
plt.imshow(Y)
plt.title("IDENTITY")

"""Du ska även testa **invers-transformen** (koefficienter-till-bild). Gör detta genom att skriva en loop som går igenom alla 64 koefficienter, och sätter en i taget till ett (övriga noll) och invers-transformerar detta tillbaka till bild-domänen. Varje pixelblock plottas till en gråskalebild med hjälp av `plt.imshow(min_bildmatris, cmap="gray")`. Du ska använda subplot för att kunna se alla på en gång - resultatet ska alltså bli en bild bestående av åtta rader och åtta kolumner av $8\times 8$-pixelblock, där det första blocket är inverstransformen av en matris av nollor och en etta i övre vänstra hörnet, det andra motsvarar en etta i andra positionen osv. Detta kan ses som en visualisering av DCT-transformens basvektorer i två dimensioner. ** (Se även slide nr. 21 i föreläsning 7) **

Försök förklara varför matrisen ser ut som den gör!
"""

# INVERS TRANSFORMEN
# T = DCT transformen, new_T = matris med 1:a på index och resten 0
index = 0
for i in range(T.shape[0]):
  for j in range(T.shape[1]):
    index += 1
    matrix = np.zeros((8,8))
    matrix[i,j] = 1
    X = T @ matrix @T.T
    plt.grid(False)
    plt.subplot(8,8, index)
    plt.imshow(X, cmap="gray")

"""## Uppgift 2: JPEG-kodaren
Skriv nu funktionen `jpeg_encode` som tar in en bildmatris $I$ (gråskala), traverserar denna i block om $8\times 8$ pixlar, beräknar 2D DCT på varje block, och sparar koefficienterna på motsvarande positioner i koefficientmatrisen $C$. Dvs, funktionen ska returnera en matris C av samma storlek som I, innehållande $8\times 8$-block av DCT-koefficienter.

För att kodningen ska fungera optimalt ska pixelvärdena centreras kring nollnivån. Du kan anta att I är en gråskalebild där varje pixel har ett värde mellan 0 och 255, vilket innebär att 128 ska subtraheras från varje pixel.

Det är tillåtet att endast räkna hela block, dvs i praktiken krympa bildens dimensioner till närmsta jämna multipel av 8.

Skriv sedan ett pythonscript för att testa din funktion: Läs in en liten bild t.ex. uggla2.tif (se tips nedan), och anropa kodar-funktionen. Plotta bilden $I$ och koefficientmatrisen $C$ sida vid sida (kolla dokumentationen eller exempel online för matplotlib, subplot osv för tips). Kofficientmatrisen kommer ha ljusa prickar i övre vänstra hörnet av varje block, och annars vara ganska mörk. I områden med skarpa kanter bör du kunna se andra koefficienter aktiveras.

*Att redovisa: python-script, funktion och plot*

>**Om bildmatriser**: I lab-introduktionen lärde vi oss hur man läser in en bildfil med paketet `imageio`, som vi redan importerat i denna colab, och funktionen `imageio.imread()`. Den läser de flesta format och returnerar en matris av pixelvärden mellan 0 och 255.   Färgbilder returneras som en $M × N × 3$-matris. I alla uppgifter utom den sista ska du jobba med *gråskala*. Färgbilder konverteras till 2D-gråskalematris genom att ta medelvärdet av de tre färgplanen. Testa t.ex. `numpy.mean()`.

Du ska  även **konvertera bildmatrisen till flyttal** med 

>`I = I.astype('float64')` 

>innan man börjar processa bilden (däremot ska du inte dela med 255 som i förra labben, eftersom kvantiseringssteget nedan bygger på att värdena ligger inom 0-255). Koefficientmatrisen $C$ ska också representeras som flyttal. För plottningen (speciellt för färgbilder i sista uppgiften) eller om man vill spara bilden på fil, behöver man gå tillbaka till **uint8**. Då måste man även se till att inga värden ligger utanför 0-255, annars kommer dessa ge felaktiga värden. Du kan använda nedanstående rad för att gå från **float64** till **uint8**:

> `I = np.clip(I,0,255).astype('uint8')`

>
"""

# Function: jpeg_encode. Encode image using block-by-block DCT-coefficients
# Input: I (nxm matrix) - Input image
# Output: C (nxm matrix) - DCT coefficient matrix
# Parameters: bs - blocksize
def jpeg_encode(I):
  # Initialize a matrix the same size as I
  C = np.zeros((I.shape[0], I.shape[1]))

  # Divide into submatrices and apply matrix operations
  bs = 8
  for p in range(0, math.floor(I.shape[0] / bs)):
      for q in range(0, math.floor(I.shape[1] / bs)):
          # Extract an 8x8 sub matrix 'Isub' from the original image 
          Isub = I[p*bs: (p+1)*bs, q*bs: (q+1)*bs]
          
          # Subtract 128 so that grayscale values (0-255) are centered around 0
          Isub = Isub - 128

          #Put matrix operation under this line
          Csub = dct_basis(bs).T @ Isub @ dct_basis(bs)

          ###
          C[p*bs: (p+1)*bs, q*bs: (q+1)*bs] =Csub
  return C

# Testa jpeg_encode() här! 
# Läs in en bild och plotta koefficientmatrisen 
uggla = imageio.imread("uggla2.tif")
uggla = uggla.astype("float64")
plt.subplot(1,2,1)
plt.imshow(uggla, cmap="gray")

C = jpeg_encode(uggla)
C = np.clip(C,0,255).astype('uint8')
plt.subplot(1,2,2)
plt.imshow(C, cmap="gray")

"""## JPEG-avkodaren

Skriv nu den kompletterande JPEG-avkodarfunktionen `jpeg_decode` som tar in koefficientmatrisen $C$ och returnerar en bildmatris $I$, vilken alltså fås fram ur den inversa DCT:n på $8\times 8$-blocken i koefficientmatrisen. Glöm inte att lägga tillbaka de 128 som du drog från varje pixel i kodaren!

Testa funktionen genom att koda en bild som du sedan kodar av och visar sida vid sida som i förra uppgiften (återanvänd testprogrammet). De två bilderna ska vara identiska (här har vi ju ännu inte slängt bort någon information).
> **Tips ang. storlek på bilder**: tycker man bilden blir för liten när man plottar kan man testa t.ex.

>`matplotlib.rcParams['figure.figsize'] = [10, 10]`

> där (10,10) är ung. bredd och höjd på bilden (i tum!:-)


*Att redovisa: Python-kod och plot*
"""

# Input: C (nxm matrix) - DCT transform matrix
# Output: I (nxm matrix) - Output image
def jpeg_decode(C):
    # Initialize a matrix the same size as C
    I = np.ones((C.shape[0], C.shape[1]))
    # Divide into submatrices and iteratively apply matrix operations
    bs = 8
    for p in range(0, math.floor(C.shape[0] / bs)):
        for q in range(0, math.floor(C.shape[1] / bs)):
            Csub = C[p*bs: (p+1)*bs, q*bs: (q+1)*bs]
            #Put matrix operation under this line
            T = dct_basis(bs)
            Isub = T @ Csub @ T.T
            ###
            Isub = Isub + 128*np.ones((bs, bs))
            I[p*bs: (p+1)*bs, q*bs: (q+1)*bs] = Isub
    return I

# Testa både encode- och decode här!
#Encode
plt.subplot(1,3,1)
plt.imshow(uggla, cmap="gray")

C = jpeg_encode(uggla)
C_plot = np.clip(C,0,255).astype('uint8')
plt.subplot(1,3,2)
plt.imshow(C_plot, cmap="gray")

#Decode
I = jpeg_decode(C)
plt.subplot(1,3,3)
plt.imshow(I, cmap="gray")

"""## Maskering och kvantisering

Som tidigare nämnts så bygger JPEG-kodning på att man kan göra sig av med stora mängder av koefficienterna, vilket inte känns helt orimligt när man tittar på koefficintmatrisen så som du gjorde i uppgift 2. Nedan beskrivs flera sätt att göra detta på, inklusive det sätt som används i JPEG-standarden.

Ett rättframt sätt att slänga information är att helt sonika bestämma vilka koefficienter som ska behållas. Vi har sagt att de viktigaste finns högt upp till vänster i sub-matriserna. Man kunde ju alltså tänka sig att multiplicera varje $8\times 8$ koefficientmatris med en mask av typen

$$\begin{matrix}
1 & 1 & 1 & 1 & 0 & 0& 0 & 0\\
1 & 1 & 1 & 0 & 0 & 0& 0 & 0\\
1 & 1 & 0 & 0 & 0 & 0& 0 & 0\\
1 & 0 & 0 & 0 & 0 & 0& 0 & 0\\
0 & 0 & 0 & 0 & 0 & 0& 0 & 0\\
0 & 0 & 0 & 0 & 0 & 0& 0 & 0\\
0 & 0 & 0 & 0 & 0 & 0& 0 & 0\\
0 & 0 & 0 & 0 & 0 & 0& 0 & 0\\
\end{matrix}
$$

Med ett sådant grepp slänger vi alltså alla utom 10 av 64 koefficinter, vilket motsvarar en kompressionsgrad av 6.4:1. Ett annat effektivt sätt kan vara att sätta en tröskel för koefficientvärdenas belopp, och sätta alla koefficienter som faller under tröskeln till noll.

Tröskeln kan vara konstant över hela bilden, men effektivare är att låta den variera block- till-block, och istället ha ett fixt antal “toppkoefficienter” från varje block.

I JPEG-standarden har man valt en något mindre drastisk metod än att rått slänga bort värdena: istället viktar man koefficinterna genom att dividera med ett förbestämt nummer och runda av till närmasta heltal. De viktiga lågfrekventa koefficinterna delas med mindre värden, och de högfrekvnta delas med större värden. Detta leder till att de höga koefficienterna oftast blir noll vid avrundningen, och kan då packas ihop effektivt av efterföljande datakodningsalgoritmer.

>**Python-tips**: För att slänga bort värden nära noll, titta på funktionen  `np.trunc()`.

De vikter man använder i standard-JPEG ges i matrisen nedan. Dessa värden är noggrant utprovade genom perceptuella försök. Genom att applicera en skalfaktor på matrisen, kan man styra hur hårt bilden ska komprimeras.

$$\begin{matrix}
16& 11& 10& 16 &24& 40& 51 &61\\
12 &12& 14& 19 &26& 58 &60& 55\\
14 &13& 16& 24& 40& 57& 69& 56\\
14 &17& 22& 29& 51& 87& 80& 62\\
18 &22& 37& 56& 68& 109& 103& 77\\
24 &35 &55& 64& 81& 104& 113 &92\\
49 &64 &78 &87 &103& 121& 120& 101\\
72 &92 &95 &98 &112& 100& 103& 99
\end{matrix}
$$

*Notera*: eftersom man delar koefficienterna med dessa värden måste samma matris användas för multiplication vid avkodningen av bilden!

## Uppgift 4: Kvantisering

Nu är det dags att börja göra sig av med koefficienter. Här får du experimentera fritt, med inspiration från texten ovan. Testa gränser. Hur blir det med bara en koefficient per block? osv. Målet är alltså att få så många nollor som möjligt, och erhålla acceptabel bildkvalitet. Skriv din kvantisering i form av en Python-funktion som tar in koefficientmatrisen och returnerar den i kvantiserad form. Du får ingen prototyp för denna funktion, eftersom den kanske ska ta ytterligare parametrar, t.ex. en kompressionsfaktor e.dyl. Gör även ett överslag på kompressionsgraden genom att räkna antalet koefficienter som inte är noll och relatera till totala antalet koefficienter.

>**Python-tips**: För att kolla antal element som inte är 0 kolla upp numpy-funktionen `count_nonzero()`.

Återanvänd testprogrammet från föregående uppgift för att plotta original och avkodad bild sida vid sida.

*Att redovisa: Python-kod för din “bästa” kvantisering, och en beskrivning av vad du provat (även “misslyckade” varianter), inkl. uppskattad kompressionsgrad och visuellt resultat!*
"""

# Weight matrix for jpeg
W = np.array([[16,11,10,16,24,40,51,61],
              [12,12,14,19,26,58,60,55],
              [14,13,16,24,40,57,69,56],
              [14,17,22,29,51,87,80,62],
              [18,22,37,56,68,109,103,77],
              [24,35,55,64,81,104,113,92],
              [49,64,78,87,103,121,120,101],
              [72,92,95,98,112,100,103,99]])

# Kod för kvantisering och testprogram här!
def kvantisering(C, W, faktor):
  # Initialize a matrix the same size as C
  D = np.zeros(C.shape)
  W = W*faktor
  # Divide into submatrices and apply matrix operations
  bs = 8
  for p in range(0, math.floor(C.shape[0] / bs)):
      for q in range(0, math.floor(C.shape[1] / bs)):
          # Extract an 8x8 sub matrix 'Csub' from the coefficients matrix 
          Csub = C[p*bs: (p+1)*bs, q*bs: (q+1)*bs]
          Dsub = np.trunc(Csub/W)
          D[p*bs: (p+1)*bs, q*bs: (q+1)*bs] = Dsub*W
  return D

# tar fram koefficient matrisen för bilden 
C = jpeg_encode(uggla)
# komprimerar C
C_kvant1 = kvantisering(C, W, 0.7)
C_kvant2 = kvantisering(C, W, 3)
C_kvant3 = kvantisering(C, W, 7)

# plottar original bilden
plt.subplot(2,3,1)
plt.imshow(uggla, cmap="gray")
plt.title("Original bild")

# plottar C utan komprimering
C_plot = np.clip(C,0,255).astype('uint8')
plt.subplot(2,3,2)
plt.imshow(C_plot, cmap="gray")
plt.title("C utan komprimering")

# plottar C med komprimering
C_kvant_plot = np.clip(C_kvant,0,255).astype('uint8')
plt.subplot(2,3,3)
plt.imshow(C_kvant_plot, cmap="gray")
plt.title("C med komprimering")

# plottar komprimerade bilden
I_comp = jpeg_decode(C_kvant1)
plt.subplot(2,3,4)
plt.imshow(I_comp, cmap="gray")
plt.title("Kompgrad =" + str((C.shape[0]*C.shape[1])/np.count_nonzero(C_kvant1)) + ":1")

# plottar komprimerade bilden
I_comp = jpeg_decode(C_kvant2)
plt.subplot(2,3,5)
plt.imshow(I_comp, cmap="gray")
plt.title("Kompgrad =" + str((C.shape[0]*C.shape[1])/np.count_nonzero(C_kvant2)) + ":1")

# plottar komprimerade bilden
I_comp = jpeg_decode(C_kvant3)
plt.subplot(2,3,6)
matplotlib.rcParams['figure.figsize'] = [15, 15]
plt.imshow(I_comp, cmap="gray")
plt.title("Kompgrad =" + str((C.shape[0]*C.shape[1])/np.count_nonzero(C_kvant3)) + ":1")

"""## Uppgift 5 (Frivillig): Färg!

Utveckla din kodare så den kan hantera färgbilder. Enligt JPEG-standarden kodas färgbilder i termer av luminans-krominans. D.v.s. innan man kan applicera DCT-algoritmen måste RGB- pixelväden omvandlas till $Y’UV$. Det sker med följande formler:
\begin{align*}Y'&= 0.299R + 0.587G + 0.114B \\
U&= −0.147R − 0.289G + 0.436B \\
V &= 0.615R − 0.515G − 0.100B
\end{align*}

och omvänt:

\begin{align*}R &= Y′ +1.13983V\\
G &= Y ′ − 0.39465U − 0.5806V \\
B &= Y ′ + 2.03211U
\end{align*}

Varje komponent kodas separat. Luminansen $(Y')$ är perceptuellt viktigare än krominansen $(U,V)$ vilket betyder att man kan använda färre bitar/hårdare kvantisering för $U$ och $V$ . Gör så att du enkelt kan kontrollera hur mycket varje komponent ska komprimeras, och experimentera med detta.
"""

image = imageio.imread("teracotta-wall.jpg")
Y = np.zeros((image.shape[0], image.shape[1]))
Cb = np.zeros((image.shape[0], image.shape[1]))
Cr = np.zeros((image.shape[0], image.shape[1]))
image.astype("float64")
def set_YCbCr(Y, Cb, Cr, img):
  for x in range(img.shape[0]):
    for y in range(img.shape[1]):
      #print(img[x,y][0])
      Y[x, y] = 0.299 * img[x, y][0] + 0.587 * img[x, y][1] + 0.114 * img[x, y][2]
      Cb[x, y] = -0.147 * img[x, y][0] - 0.289 * img[x, y][1] + 0.436 * img[x, y][2]
      Cr[x, y] = 0.615 * img[x, y][0] - 0.515 * img[x, y][1] - 0.100 * img[x, y][2]

def set_RGB(Y, Cb, Cr):
  img_compressed = np.zeros((Y.shape[0], Y.shape[1], 3))
  for x in range(Y.shape[0]):
    for y in range(Y.shape[1]):
      img_compressed[x, y][0] = Y[x, y] + 1.13983*Cr[x, y]
      img_compressed[x, y][1] = Y[x, y] - 0.39465*Cb[x, y] - 0.5806*Cr[x, y]
      img_compressed[x, y][2] = Y[x, y] + 2.03211*Cb[x, y]
  return img_compressed

set_YCbCr(Y, Cb, Cr, image)

# applicerar DCT
Y_C = jpeg_encode(Y)
Cb_C = jpeg_encode(Cb)
Cr_C = jpeg_encode(Cr)

# komprimerar koefficientmatrisen
Y_C_kvant = kvantisering(Y_C, W, 1)
Cb_C_kvant = kvantisering(Cb_C, W, 5)
Cr_C_kvant = kvantisering(Cr_C, W, 5)

# applicerar IDCT
Y_comp = jpeg_decode(Y_C_kvant)
Cb_comp = jpeg_decode(Cb_C_kvant)
Cr_C_comp = jpeg_decode(Cr_C_kvant)

# omvandlar till RGB

comp_picture = set_RGB(Y_comp, Cb_comp, Cr_C_comp)
comp_picture = np.clip(comp_picture,0,255).astype('uint8')
plt.imshow(comp_picture)