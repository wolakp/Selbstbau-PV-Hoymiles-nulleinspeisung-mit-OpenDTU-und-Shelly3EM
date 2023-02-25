import requests, time
from requests.auth import HTTPBasicAuth

# Diese Daten müssen angepasst werden: zeile 5 - 12
serial      = "112100000000"    # Seriennummern der Hoymiles Wechselrichter
maximum_wr  = 1500              # Maximum ausgabe des wechselrichters
zielwert    = 20                # geplanter Bezug aus Netz
obere_abw   = 15                # erlaubte Abweichung über den Zielwert
untere_abw  = 15                # erlaubte Abweichung unter den Zielwert

dtuIP = '192.168.168.97' # IP Adresse von OpenDTU
dtuNutzer = 'admin' # OpenDTU Nutzername
dtuPasswort = 'openDTU42' # OpenDTU Passwort

shellyIP = '192.168.168.195' #IP Adresse von Shelly 3EM


while True:
    # Nimmt Daten von der openDTU Rest-API und übersetzt sie in ein json-Format
    r = requests.get(url = f'http://{dtuIP}/api/livedata/status/inverters' ).json()

    # Selektiert spezifische Daten aus der json response
    reachable   = r['inverters'][0]['reachable'] # ist DTU erreichbar ?
    producing   = int(r['inverters'][0]['producing']) # produziert der Wechselrichter etwas ?
    altes_limit = int(r['inverters'][0]['limit_absolute']) # wo war das alte Limit gesetzt
    power_dc    = r['inverters'][0]['0']['Power DC']['v']  # Lieferung DC vom Panel
    power       = r['inverters'][0]['0']['Power']['v'] # Abgabe BKW AC in Watt

    # Nimmt Daten von der Shelly 3EM Rest-API und übersetzt sie in ein json-Format
    # phaseA      = requests.get(f'http://{shellyIP}/emeter/0', headers={"Content-Type": "application/json"}).json()['power']
    # phaseB      = requests.get(f'http://{shellyIP}/emeter/1', headers={"Content-Type": "application/json"}).json()['power']
    # phaseC      = requests.get(f'http://{shellyIP}/emeter/2', headers={"Content-Type": "application/json"}).json()['power']
    # grid_sum    = phaseA + phaseB + phaseC # Aktueller Bezug im Chalet - rechnet alle Phasen zusammen
    grid_sum    = requests.get(f'http://{shellyIP}/status', headers={"Content-Type": "application/json"}).json()['total_power']

    # Setzt ein limit auf den Wechselrichter
    def setLimit(Serial, Limit):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = f'''data={{"serial":"{Serial}", "limit_type":1, "limit_value":{Limit}}}'''
        newLimit = requests.post(url=f'http://{dtuIP}/api/limit/config', data=payload, auth=HTTPBasicAuth(dtuNutzer, dtuPasswort), headers=headers)
        print('Konfiguration Stauts:', newLimit.json()['type'])

    # Werte setzen
    print("aktueller Bezug - Haus:   ", grid_sum)
    verbrauch   = power + grid_sum
    print("aktueller Verbrauch:   ", verbrauch)
    setpoint    = verbrauch - zielwert
    print("neues Limit berechnet auf: ",verbrauch," - ",zielwert," = ", setpoint)
    if reachable:
        # Setzen Sie den Grenzwert auf den höchsten Wert, wenn er über dem zulässigen Höchstwert liegt.
        if ( setpoint >= maximum_wr ):
            print("setze Maximum: ", maximum_wr)
            setpoint = maximum_wr

        # falls setpoint zu weit vom aktuellen Limit abweicht
        if ( setpoint < altes_limit - untere_abw or setpoint > altes_limit + obere_abw ):
            print("setze Wechselrichterlimit auf: ", setpoint)
            # neues limit setzen
            setLimit(serial, setpoint)
            print("Solarzellenstrom: ",power,"  Setpoint: ",setpoint)
        time.sleep(5) # wait
