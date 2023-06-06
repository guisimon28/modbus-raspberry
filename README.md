
# Pilotage d'équipement via Modbus

projet raspberry pour le pilotage d'équipement Modbus

## Installation

### Système d'exploitation 

Installer un os raspberry depuis Raspberry imager (https://www.raspberrypi.com/software/). J'ai choisi un os sans desktop et activé le ssh dans les options avancées

### Librairies

Installer le gestionnaire de package pour python via la commande suivante

    sudo apt install python3-pip
   
   Lancer la commande suivante pour installer les librairies utilisées par le projet
   

    pip install pymodbus RPi.GPIO psutil twisted

Pour piloter l'afficheur lcd, nous avons besoin d'utiliser une librairie tierce. Se placer dans le mêmes répertoire que le script python initial et exécuter les commandes suivantes 

    wget http://tutorials-raspberrypi.de/wp-content/uploads/scripts/hd44780_i2c.zip
    unzip hd44780_i2c.zip

En executant la commande suivante 

    pip freeze
On doit obtenir le résultat suivant 
    
    attrs==23.1.0
    Automat==22.10.0
    certifi==2020.6.20
    chardet==4.0.0
    colorzero==1.1
    constantly==15.1.0
    distro==1.5.0
    gpiozero==1.6.2
    hyperlink==21.0.0
    idna==2.10
    incremental==22.10.0
    numpy==1.19.5
    picamera2==0.3.9
    pidng==4.0.9
    piexif==1.1.3
    Pillow==8.1.2
    psutil==5.9.5
    pymodbus==3.3.1
    pyserial==3.5
    python-apt==2.2.1
    python-prctl==1.7
    requests==2.25.1
    RPi.GPIO==0.7.0
    simplejpeg==1.6.4
    six==1.16.0
    spidev==3.5
    ssh-import-id==5.10
    toml==0.10.1
    Twisted==22.10.0
    typing-extensions==4.6.3
    urllib3==1.26.5
    v4l2-python3==0.3.2
    zope.interface==6.0

### Ip statique

Editer le fichier suivant 

    sudo nano /etc/dhcpcd.conf
Rempacer les lignes suivantes 

    interface  eth0  
    static ip_address=192.168.1.100/24  
    static routers=192.168.1.1  
    static domain_name_servers=192.168.1.1
Assurez-vous d'utiliser les valeurs appropriées pour votre réseau.
Redémarrez votre Raspberry Pi pour que les nouvelles configurations prennent effet :

    sudo reboot



