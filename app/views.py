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

from app.biblioteca_SEA import Reles

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

rele = Reles()

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


def temperatura():
    temp = os.popen("vcgencmd measure_temp").readline()
    mem = os.popen("vcgencmd get_mem arm").readline()
    
    for linha in os.popen("df -h /home/pi"):
        linha = linha    
        
    temp = temp.split("=")[1]
    temp = temp.split(".")[0]    
    
    print("temperatura cpu",temp)
    dados = {"temperatura":temp}    

    return dados

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


@app.route('/atualiza',methods=['GET'])
def atualiza():
        
    temp = os.popen("vcgencmd measure_temp").readline()
    mem = os.popen("vcgencmd get_mem arm").readline()
    
    for linha in os.popen("df -h /home/pi"):
        linha = linha    
        
    temp = temp.split("=")[1]
    temp = temp.split(".")[0]

    temp = os.popen("vcgencmd measure_temp").readline()
    mem = os.popen("vcgencmd get_mem arm").readline()
    
    for linha in os.popen("df -h /home/pi"):
        linha = linha    
        
    temp = temp.split("=")[1]
    temp = temp.split(".")[0] 
    
    temperatura = temp   

    dados = {"temperatura": temperatura}

    return dados

@app.route('/reles',methods=['GET', 'POST'])
def reles():
    
    r = request.args
    print("Argumentos recebidos",r)
        
    if "switch1_on" in r:           
        rele.rele1_on()
        session['rele1'] = True 
    if 'switch1_off' in r:        
        rele.rele1_off()
        session['rele1'] = False

    if "switch2_on" in r:           
        rele.rele2_on()
    if 'switch2_off' in r:        
        rele.rele2_off()

    if "switch3_on" in r:           
        rele.rele3_on() 
    if 'switch3_off' in r:        
        rele.rele3_off()

    if "switch4_on" in r:           
        rele.rele4_on() 
    if 'switch4_off' in r:        
        rele.rele4_off()

    if "switch5_on" in r:           
        rele.rele5_on()
    if 'switch5_off' in r:        
        rele.rele5_off()

    if "switch6_on" in r:           
        rele.rele6_on()
    if 'switch6_off' in r:        
        rele.rele6_off()

    if "switch7_on" in r:           
        rele.rele7_on()
    if 'switch7_off' in r:        
        rele.rele7_off()

    if "switch8_on" in r:           
        rele.rele8_on() 
    if 'switch8_off' in r:        
        rele.rele8_off()

    if "switch9_on" in r:           
        rele.rele9_on()
    if 'switch9_off' in r:        
        rele.rele9_off()

    if "switch10_on" in r:           
        rele.rele10_on() 
    if 'switch10_off' in r:        
        rele.rele10_off()

    if "switch11_on" in r:           
        rele.rele11_on() 
    if 'switch11_off' in r:        
        rele.rele11_off()

    if "switch12_on" in r:           
        rele.rele12_on()
    if 'switch12_off' in r:        
        rele.rele12_off()    
        
    if "switch13_on" in r:         
        rele.rele13_on() 
    if 'switch13_off' in r:        
        rele.rele13_off() 

    if "rele1" in r:
        rele.rele1_on()     
        time.sleep(2)
        rele.rele1_off()
        # session['rele1'] = False 

    if "rele2" in r:
        rele.rele2_on()     
        time.sleep(2)
        rele.rele2_off() 

    if "rele3" in r:
        rele.rele3_on()     
        time.sleep(2)
        rele.rele3_off() 

    if "rele4" in r:
        rele.rele4_on()     
        time.sleep(2)
        rele.rele4_off() 

    if "rele5" in r:        
        rele.rele5_on()     
        time.sleep(2)
        rele.rele5_off()
        
    if "rele6" in r:
        rele.rele6_on()     
        time.sleep(2)
        rele.rele6_off()

    if "rele7" in r:
        rele.rele7_on()     
        time.sleep(2)
        rele.rele7_off()

    if "rele8" in r:
        rele.rele8_on()     
        time.sleep(2)
        rele.rele8_off() 

    if "rele9" in r:
        rele.rele9_on()     
        time.sleep(2)
        rele.rele9_off() 

    if "rele10" in r:
        rele.rele10_on()     
        time.sleep(2)
        rele.rele10_off()    

    if "rele11" in r:
        rele.rele11_on()     
        time.sleep(2)
        rele.rele11_off()

    if "rele12" in r:
        rele.rele12_on()     
        time.sleep(2)
        rele.rele12_off()         

    if "rele13" in r:
        rele.rele13_on()     
        time.sleep(2)
        rele.rele13_off()

    if "reiniciar" in r:
        print("REINICIANDO O SISTEMA...")
        os.system("sudo reboot now") 
    
       
    dados = {"rele1" : "ok"}
                # "rele2" : rele2,
                # "rele3" : rele3,
                # "rele4" : rele4,
                # "rele5" : rele5,
                # "rele6" : rele6,
                # "rele7" : rele7,
                # "rele8" : rele8,
                # "rele9" : rele9,
                # "rele10" : rele10,
                # "rele11" : rele11,
                # "rele12" : rele12,
                # "rele13" : rele13,
                # "rele1" : rele1,
                # "rele1" : rele1,
                # "rele1" : rele1,
                # "rele1" : rele1,
                # "rele1" : rele1,
                # "temperatura" : temperatura,
                # "espaco" : espaco,
                # "memoria" : memoria                 
                #  }

    return dados

       
    
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
