from lanzatw import Game
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import os
g = Game()


lista =  g.db.getListaTabla() 
conquistas = [n[1] for n in lista]
carreras = list(set([n[0] for n in lista]))

killer_count = 0
longest_name = ""

for n in carreras:
    num_conquistas =  conquistas.count(n) 
    if len(longest_name) < len(n): longest_name = n
    if killer_count < num_conquistas: killer_count = num_conquistas

altura = len(lista)*20+32
ancho  = (len(longest_name)+len(str(len(lista))))*8+32

img = Image.new('RGB', (ancho,int(altura)), color = "white")
draw = ImageDraw.Draw(img)
filename = "lista.jpg"
font = ImageFont.truetype("sans-serif.ttf", 16)

y = 16
deps = []
for n in sorted(carreras):

    color = (0,0,0,255)

    nombre = n
    num_conquistas =  conquistas.count(n)
    
    if num_conquistas == killer_count: color = (26, 135, 231, 1)
    if num_conquistas == 0:
        deps.append(n)
        continue

    draw.text((4, y),f"{nombre}",fill=color,font=font)
    draw.text((ancho-len(str(len(lista)))*8-4, y), str(num_conquistas) , fill=color, font=font)

    y += 20

for nombre in deps:
    color = (231, 76, 60, 1)
    draw.text((4, y),f"{nombre}",fill=color,font=font)
    draw.text((ancho-len(str(len(lista)))*8-16, y), "dep" , fill=color, font=font)

img.save(filename)

g.tw.listaVivos(filename)

