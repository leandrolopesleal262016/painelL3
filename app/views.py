# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 
import random
# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort

# App modules
from app        import app, lm, db#, bc
from app.models import User
from app.forms  import LoginForm, RegisterForm
import socket

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

# provide login manager with load_user callback
@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Logout user
@app.route('/logout.html')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register a new user
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    
    # cut the page for authenticated users
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # declare the Registration Form
    form = RegisterForm(request.form)

    msg = None

    if request.method == 'GET': 

        return render_template( 'pages/register.html', form=form, msg=msg )

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 
        email    = request.form.get('email'   , '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        # filter User out of database through username
        user_by_email = User.query.filter_by(email=email).first()

        if user or user_by_email:
            msg = 'Error: User exists!'
        
        else:         

            pw_hash = password #bc.generate_password_hash(password)

            user = User(username, email, pw_hash)

            user.save()

            msg = 'User created, please <a href="' + url_for('login') + '">login</a>'     

    else:
        msg = 'Input error'     

    return render_template( 'pages/register.html', form=form, msg=msg )

# Authenticate user
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    
    # cut the page for authenticated users
    if current_user.is_authenticated:
        return redirect(url_for('index'))
            
    # Declare the login form
    form = LoginForm(request.form)

    # Flask message injected into the page, in case of any errors
    msg = None

    # check if both http method is POST and form is valid on submit
    if form.validate_on_submit():

        # assign form data to variables
        username = request.form.get('username', '', type=str)
        password = request.form.get('password', '', type=str) 

        # filter User out of database through username
        user = User.query.filter_by(user=username).first()

        if user:
            
            #if bc.check_password_hash(user.password, password):
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
            else:
                msg = "Wrong password. Please try again."
        else:
            msg = "Unknown user"

    return render_template( 'pages/login.html', form=form, msg=msg )

@app.route('/nomes_reles',methods=['POST'])
def nomes_reles():
    nomes = request.form
    print(nomes)

@app.route('/',methods=['GET', 'POST'])
def index():

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    temp = os.popen("vcgencmd measure_temp").readline()
    mem = os.popen("vcgencmd get_mem arm").readline()
    
    for linha in os.popen("df -h /home/pi"):
        linha = linha
    
    linha = linha.split(" ")
    linha = linha[-2]
    linha = str(linha)
    hd = linha.replace("%","")
    
    temp = temp.split("=")[1]
    temp = temp.split(".")[0]
    mem = mem.split("=")[1]
    mem = mem.replace("M","")
    mem = int(mem)
    mem = round(mem/10)
    
    print("temperatura cpu",temp)
    print("memoria",mem)
    print("Espaço utilizado",hd)
    
    
    temperatura = temp
    espaco = hd
    memoria = mem
    ip = os.popen('hostname -I').readline()
    ip = str(ip)
    ip = ip.replace("\n","")
    ip = ip.split(" ")
    ip1 = ip[0]
    ip2 = ip[1]
    print("Nome desta maquina",ip1,ip2)

    return render_template( 'pages/index.html', temperatura=temperatura, ip = ip1,
                            espaco = espaco, memoria = memoria)

@app.route('/reles',methods=['GET', 'POST'])
def reles():

    r = request.args

    saidaA = 0b00000000  # Zera as saidas do port A (saidas do rele 1 ao rele 8 )
    saidaB = 0b00000000  # Zera as saidas do port B (saidas dos reles 9 e 10 e dos transistors 11,12,13)

    if "rele1" in r:

        print("Acionando rele1 ")        
        saidaA = saidaA + 0b00000001  # aciona rele 1 (abre portão social)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00000001  # aciona rele 1 (abre portão social)
        bus.write_byte_data(MCP23017, 0x014, saidaA)

    if "rele2" in r:

        print("Acionando rele2 ")  
        saidaA = saidaA + 0b00000010  # aciona rele 2 (abre portão eclusa)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00000010  # aciona rele 2 (abre portão eclusa)
        bus.write_byte_data(MCP23017, 0x014, saidaA)

    if "rele3" in r:

        print("Acionando rele3 ")  
        saidaA = saidaA + 0b00000100  # aciona rele 3 (FOTO portão social)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00000100  # aciona rele 3 (FOTO portão social)
        bus.write_byte_data(MCP23017, 0x014, saidaA)


    if "rele4" in r:

        print("Acionando rele4 ")  
        saidaA = saidaA + 0b00001000  # aciona rele 4 (FOTO portão eclusa)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00001000  # aciona rele 4 (FOTO portão eclusa)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        

    if "rele5" in r:

        print("Acionando rele5 ")  
        saidaA = saidaA + 0b00010000   # aciona rele 5
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00010000  
        bus.write_byte_data(MCP23017, 0x014, saidaA)

        
    if "rele6" in r:

        print("Acionando rele6 ")  
        saidaA = saidaA + 0b00100000   # aciona rele 6
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00100000  
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        

    if "rele7" in r:

        print("Acionando rele7 ")  
        saidaA = saidaA + 0b01000000   # aciona rele 7
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b01000000  
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        

    if "rele8" in r:

        print("Acionando rele8 ")  
        saidaA = saidaA + 0b10000000  # aciona rele 8
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b10000000  
        bus.write_byte_data(MCP23017, 0x014, saidaA)


    if "rele9" in r:

        print("Acionando rele9 ")          
        saidaB = saidaB + 0b00000001  # aciona rele 9 
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00000001  
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        

    if "rele10" in r:

        print("Acionando rele10 ")  
        saidaB = saidaB + 0b00000010  # aciona rele 10 
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00000010 
        bus.write_byte_data(MCP23017, 0x015, saidaB)   

    if "rele11" in r:

        print("Acionando transistor 1 ")  
        saidaB = saidaB + 0b00000100  # liga LED AZUL saida GPB3
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00000100  
        bus.write_byte_data(MCP23017, 0x015, saidaB)        


    if "rele12" in r:

        print("Acionando transistor 2 ")  
        saidaB = saidaB + 0b00001000  # desliga LED VERMELHO saida GPB3
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00001000  
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        

    if "rele13" in r:

        print("Acionando transistor 3 ")          
        saidaB = saidaB + 0b00010000  # liga cooler
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00010000  
        bus.write_byte_data(MCP23017, 0x015, saidaB)     
        
    
    if "teste_reles" in r:
    
        print("Acionando saidas dos reles")
        

        bus.write_byte_data(MCP23017, 0x015, 0)  # Zera saidas do port B
        bus.write_byte_data(MCP23017, 0x014, 0)  # Coloca todas as saidas do PORT A em 0

        
        saidaA = saidaA + 0b00000001  # aciona rele 1 (abre portão social)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00000001  # aciona rele 1 (abre portão social)
        bus.write_byte_data(MCP23017, 0x014, saidaA)

        time.sleep(1)

        saidaA = saidaA + 0b00000010  # aciona rele 2 (abre portão eclusa)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00000010  # aciona rele 2 (abre portão eclusa)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        
        time.sleep(1)

        saidaA = saidaA + 0b00000100  # aciona rele 3 (FOTO portão social)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00000100  # aciona rele 3 (FOTO portão social)
        bus.write_byte_data(MCP23017, 0x014, saidaA)

        time.sleep(1)

        saidaA = saidaA + 0b00001000  # aciona rele 4 (FOTO portão eclusa)
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00001000  # aciona rele 4 (FOTO portão eclusa)
        bus.write_byte_data(MCP23017, 0x014, saidaA)

        time.sleep(1)   

        saidaA = saidaA + 0b00010000   # aciona rele 5
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00010000  
        bus.write_byte_data(MCP23017, 0x014, saidaA)

        time.sleep(1)

        saidaA = saidaA + 0b00100000   # aciona rele 6
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b00100000  
        bus.write_byte_data(MCP23017, 0x014, saidaA)

        time.sleep(1)

        saidaA = saidaA + 0b01000000   # aciona rele 7
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b01000000  
        bus.write_byte_data(MCP23017, 0x014, saidaA)

        time.sleep(1)

        saidaA = saidaA + 0b10000000  # aciona rele 8
        bus.write_byte_data(MCP23017, 0x014, saidaA)
        time.sleep(1)
        saidaA = saidaA - 0b10000000  
        bus.write_byte_data(MCP23017, 0x014, saidaA)

        time.sleep(1)

        saidaB = saidaB + 0b00000001  # aciona rele 9 
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00000001  
        bus.write_byte_data(MCP23017, 0x015, saidaB)

        time.sleep(1)

        saidaB = saidaB + 0b00000010  # aciona rele 10 
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00000010 
        bus.write_byte_data(MCP23017, 0x015, saidaB)   

        time.sleep(1)

        saidaB = saidaB + 0b00000100  # liga LED AZUL saida GPB3
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00000100  
        bus.write_byte_data(MCP23017, 0x015, saidaB)

        time.sleep(1)

        saidaB = saidaB + 0b00001000  # desliga LED VERMELHO saida GPB3
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00001000  
        bus.write_byte_data(MCP23017, 0x015, saidaB)

        time.sleep(1)

        saidaB = saidaB + 0b00010000  # liga cooler
        bus.write_byte_data(MCP23017, 0x015, saidaB)
        time.sleep(1)
        saidaB = saidaB - 0b00010000  
        bus.write_byte_data(MCP23017, 0x015, saidaB)     

        return redirect(url_for('index'))

    return redirect(url_for('index'))
    
    
@app.route('/', defaults={'path': 'index_original.html'})
@app.route('/<path>')
def index2(path):

    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    content = None

    try:

        # try to match the pages defined in -> pages/<input file>
        return render_template( 'pages/'+path )
    
    except:
        
        return render_template( 'pages/error-404.html' )

# Return sitemap 
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')
