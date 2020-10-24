
# !/usr/bin/env/ python3
# -*- coding:utf-8 -*-

from gtts import gTTS  # importamos o modúlo gTTS
import pygame  # Permite a utilização do modulo para execução de mp3
import time  # Funções de tempo
import RPi.GPIO as GPIO
import smbus  # para funcionamento dos módulos com interface I2C
import spidev
import os  # Permite a execução de comandos do sistema operacional dentro do script Ex.: os.system('sudo reboot now')
import threading  # Modulo superior Para executar as threads


GPIO.setwarnings(False)  # desabilita mensagens de aviso
GPIO.setmode(GPIO.BCM)  # Modo de endereço dos pinos BCM
spi = spidev.SpiDev()  # Parametros da configuração da comunicação SPI (Entrada Portas Analógcas)
spi.open(0, 0)
spi.max_speed_hz = 1000000
pygame.init()  # Inicia o pygame para uso do módulo de voz
pygame.mixer.music.set_volume(0.1)  # Ajusta o volume geral das narrações do modulo de voz
bus = smbus.SMBus(1)  # Parametros de configuração do módulo MCP23017 - SAIDA DOS RELÊS via I2C
MCP23017 = 0X20  # Endereço do módulo de saidas dos reles
MCP3008 = 0
bus.write_byte_data(MCP23017, 0x00, 0x00)  # defina todo GPA como saida 0x00
bus.write_byte_data(MCP23017, 0x01, 0x00)  # defina todo GPB como saida 0x01

# Define os pinos que serão entradas:

GPIO.setup(17, GPIO.IN)  # GPIO0 (in 1)
GPIO.setup(18, GPIO.IN)  # GPIO1 (in 2)
GPIO.setup(27, GPIO.IN)  # GPIO2 (in 3)
GPIO.setup(22, GPIO.IN)  # GPIO3 (in 4)
GPIO.setup(23, GPIO.IN)  # gpio4 (in 5)
GPIO.setup(24, GPIO.IN)  # GPIO5 (in 6)
GPIO.setup(25, GPIO.IN)  # GPIO6 (in 7)
GPIO.setup(4, GPIO.IN)   # GPIO7 (in 8)

IN1 = GPIO.input(17)
IN2 = GPIO.input(18)
IN3 = GPIO.input(27)
IN4 = GPIO.input(22)
IN5 = GPIO.input(23)
IN6 = GPIO.input(24)
IN7 = GPIO.input(25)
IN8 = GPIO.input(4)

saidaA = 0b00000000  # Zera as saidas do port A (saidas do rele 1 ao rele 8 )
saidaB = 0b00000000  # Zera as saidas do port B (saidas dos reles 9 e 10 e dos transistors 11,12,13)

bus.write_byte_data(MCP23017, 0x015, 0)  # Zera saidas do port B
bus.write_byte_data(MCP23017, 0x014, 0)  # Coloca todas as saidas do PORT A em 0


########################## Tradução dos dias da semana para módulo de voz caso usar GTTS (somente online)

if (time.strftime("%A") == "Sunday"):
    dia_da_semana = "Domingo"

if (time.strftime("%A") == "Monday"):
    dia_da_semana = "Segunda feira"

if (time.strftime("%A") == "Tuesday"):
    dia_da_semana = "Terça feira"

if (time.strftime("%A") == "Wednesday"):
    dia_da_semana = "Quarta feira"

if (time.strftime("%A") == "Thursday"):
    dia_da_semana = "Quinta feira"

if (time.strftime("%A") == "Friday"):
    dia_da_semana = "Sexta feira"

if (time.strftime("%A") == "Saturday"):
    dia_da_semana = "Sábado"

hs = time.strftime("%H:%M:%S")  # Hora completa para registro de Log
hora = time.strftime('%H:%M')
h = int(time.strftime('%H'))
dia_mes = time.strftime("%d")
y = time.strftime("%Y")
m = time.strftime("%m")
data = time.strftime('%d/%m/%y')


# Rotina para GTTS (API Text to Spech do Google)

def dia_e_hora(hora):
    if (h < 12):
        periodo = "Bom dia!"

    if (h > 12 and h < 18):
        periodo = "Boa tarde!"

    if (h >= 18 and h <= 23):
        periodo = "Boa noite!"

    voz = gTTS(periodo, lang="pt")
    voz.save("periodo.mp3")
    voz = gTTS("Agora são", lang="pt")
    voz.save("voz_hora.mp3")
    voz = gTTS(hora, lang="pt")
    voz.save("voz_hora1.mp3")

    pygame.mixer.music.load('voz_hora.mp3')
    pygame.mixer.music.play()
    time.sleep(1.2)
    pygame.mixer.music.load('voz_hora1.mp3')
    pygame.mixer.music.play()
    time.sleep(2.5)


# Rotina para GTTS

def dia_semana(dia_da_semana):
    voz = gTTS("e hoje é", lang="pt")
    voz.save("hoje_e.mp3")
    voz = gTTS(dia_da_semana, lang="pt")
    voz.save("dia_semana.mp3")

    pygame.mixer.music.load('hoje_e.mp3')
    pygame.mixer.music.play()
    time.sleep(1.05)
    pygame.mixer.music.load('dia_semana.mp3')
    pygame.mixer.music.play()
    time.sleep(2)


# Rotina para GTTS

def dia_do_mes(dia_mes):
    voz = gTTS(dia_mes, lang="pt")
    voz.save("dia_mes.mp3")
    pygame.mixer.music.load('dia_mes.mp3')
    pygame.mixer.music.play()
    time.sleep(2)

# Rotina para GTTS

def narrador(mensagem):
    try:

        voz = gTTS(mensagem, lang="pt")  # guardamos o nosso texto na variavel voz
        voz.save("mensagem.mp3")  # salvamos com o comando save em mp3
        pygame.mixer.music.load('mensagem.mp3')
        pygame.mixer.music.play()
        print("Reproduzindo Texto no narrador")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        print("terminou o narração")

    except:

        print("narrador não esta funcionando")


# Função que obtem o valor da entrada analógica e converte para 1 ou 0 (1 > 800, max 1023 3.3v)
#  - para esta função usar divisor de tensão na entrada analógica para reduzir a tensão para até no máximo 3.3v

def readadc(
        adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.
    if ((adcnum > 7) or (adcnum < 0)):
        return -1
    r = spi.xfer2([1, (8 + adcnum) << 4, 0])
    adcout = ((r[1] & 3) << 8) + r[2]
    if (adcout > 600):
        adcout = 1
    else:
        adcout = 0
    return adcout


def get_cpu_temp():  # retorna o valor da temperatura da cpu do CLP
    tempFile = open("/sys/class/thermal/thermal_zone0/temp")
    cpu_temp = tempFile.read()
    tempFile.close()
    return float(cpu_temp) / 1000


def saudacao():

    if (h < 12):

        print("Bom dia")

        pygame.mixer.music.load('mp3/010.mp3')  # Bom dia
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    if (h >= 12 and h < 18):

        print("Boa tarde")

        pygame.mixer.music.load('mp3/009.mp3')  # Boa tarde
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

    if (h >= 18):

        print("Boa noite")

        pygame.mixer.music.load('mp3/150.mp3')  # Boa noite
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

def reproduz_som():

    pygame.mixer.music.load('mp3/049.mp3')  # Espere o fechamento do primeiro portão
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

class Reles():

    def __init__(self):

        self.saidaA = 0b00000000  # Zera as saidas do port A (saidas do rele 1 ao rele 8 )
        self.saidaB = 0b00000000  # Zera as saidas do port B (saidas dos reles 9 e 10 e dos transistors 11,12,13)

        bus.write_byte_data(MCP23017, 0x015, 0)  # Zera saidas do port B
        bus.write_byte_data(MCP23017, 0x014, 0)  # Coloca todas as saidas do PORT A em 0
   
    def rele1_on(self):
        self.saidaA = self.saidaA + 0b00000001  # aciona rele 1
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)

    def rele1_off(self):        
        self.saidaA = self.saidaA - 0b00000001  # desaciona rele 1
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)

    def rele2_on(self):
        self.saidaA = self.saidaA + 0b00000010  # aciona rele 2 
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)

    def rele2_off(self):
        self.saidaA = self.saidaA - 0b00000010  # aciona rele 2 
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele3_on(self):
        self.saidaA = self.saidaA + 0b00000100  # aciona rele 3 
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)

    def rele3_off(self):
        self.saidaA = self.saidaA - 0b00000100  # aciona rele 3 
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele4_on(self):
        self.saidaA = self.saidaA + 0b00001000  # aciona rele 4 
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
        
    def rele4_off(self):
        self.saidaA = self.saidaA - 0b00001000  # aciona rele 4 
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
       
    def rele5_on(self):
        self.saidaA = self.saidaA + 0b00010000   # aciona rele 5
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele5_off(self):
        self.saidaA = self.saidaA - 0b00010000  
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele6_on(self):
        self.saidaA = self.saidaA + 0b00100000   # aciona rele 6
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele6_off(self):
        self.saidaA = self.saidaA - 0b00100000  
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele7_on(self):
        self.saidaA = self.saidaA + 0b01000000   # aciona rele 7
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele7_off(self):
        self.saidaA = self.saidaA - 0b01000000  
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele8_on(self):
        self.saidaA = self.saidaA + 0b10000000  # aciona rele 8
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele8_off(self):
        self.saidaA = self.saidaA - 0b10000000  
        bus.write_byte_data(MCP23017, 0x014, self.saidaA)
    
    def rele9_on(self):
        self.saidaB = self.saidaB + 0b00000001  # aciona rele 9 
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele9_off(self):
        self.saidaB = self.saidaB - 0b00000001  
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele10_on(self):
        self.saidaB = self.saidaB + 0b00000010  # aciona rele 10 
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele10_off(self):
        self.saidaB = self.saidaB - 0b00000010 
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele11_on(self):
        self.saidaB = self.saidaB + 0b00000100  # liga LED AZUL saida GPB3
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele11_off(self):
        self.saidaB = self.saidaB - 0b00000100  
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele12_on(self):
        self.saidaB = self.saidaB + 0b00001000  # desliga LED VERMELHO saida GPB3
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele12_off(self):
        self.saidaB = self.saidaB - 0b00001000  
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele13_on(self):
        self.saidaB = self.saidaB + 0b00010000  # liga cooler
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
    
    def rele13_off(self):
        self.saidaB = self.saidaB - 0b00010000  
        bus.write_byte_data(MCP23017, 0x015, self.saidaB)
     

   

    


