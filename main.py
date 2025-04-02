from fastapi import FastAPI, HTTPException
from datetime import datetime
import requests
import csv
from io import StringIO
from pydantic import BaseModel
from typing import Optional
import os
import pywhatkit as pkt
from infobip_channels.whatsapp.channel import WhatsAppChannel
import time
from bs4 import BeautifulSoup


app = FastAPI()


def buscar_archivo_en_drive(folder_url, target_file):
    folder_id = folder_url.split("/")[-1]
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return "Error al acceder a la carpeta."
    
    soup = BeautifulSoup(response.text, "html.parser")
    found_files = []
    
    # Buscar en todas las entradas de archivos
    for entry in soup.select("div.flip-entry"):
        # Extraer el nombre del archivo (está en un div con clase "flip-entry-title")
        file_name_element = entry.select_one(".flip-entry-title")
        if file_name_element:
            file_name = file_name_element.text.strip()
            # Extraer el ID del archivo (está en el atributo "id" del div principal, ejemplo: "entry-17JGhpkb2_0s4yNMyhEXZWbs5ekEQwhyZ")
            file_id = entry.get("id").replace("entry-", "") if entry.get("id") else ""
            
            if target_file.lower() in file_name.lower():  # Búsqueda insensible a mayúsculas
                found_files.append({
                    "name": file_name,
                    "url": f"https://drive.google.com/file/d/{file_id}/view"
                })
    
    return file_id, found_files

class WhatsAppResponse(BaseModel):
    status: str
    message: str
    image_url: Optional[str] = None
    timestamp: str

def get_public_sheet_data(sheet_url: str):
    try:
        session = requests.Session()
        response = session.get(
            sheet_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Decodificar el contenido
        content = response.content.decode("utf-8-sig")
        csv_data = StringIO(content)
        
        return list(csv.DictReader(csv_data))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al leer Google Sheet: {str(e)}"
        )
        

def send_whatsapp_image(image_url: str, name: str, phone) -> bool:
    print(name)
    print(phone)
    params = {
        "recipient": f"57{phone}",  # Sin el "+"
        "apikey": "oUAms4QCxndG",
        "text": f'''🎉 ¡Feliz Cumpleaños! 🎉
Estimado(a) {name},

Hoy, desde el Partido MIRA , queremos honrar su liderazgo y visión con un mensaje lleno de admiración. Su ejemplo de vida, guiado por principios de justicia, libertad y respeto a la vida, ha sido un faro de inspiración para todos quienes aspiramos a un Colombia mejor.

Que este día esté impregnado de la paz, esperanza y alegría que usted ha sembrado en quienes le siguen. Su trayectoria, marcada por un compromiso inquebrantable con la democracia y el bien común, demuestra que el verdadero liderazgo transforma realidades.

¡Que Dios le conceda salud, fuerzas y sabiduría para seguir iluminando el camino hacia un futuro de oportunidades! 🙏

Con profundo respeto y gratitud,
Partido MIRA 🇨🇴❤️
Por un país con valores, libertad y progreso.''',
        "file": image_url
        
    }
    
    try:
        response = requests.get(
            "https://api.textmebot.com/send.php",
            params=params,
            timeout=60
        )
        
        # DEBUG: Inspecciona la solicitud
        print("\nURL completa enviada a textmebot:")
        print(response.request.url)  # Muestra la URL real usada
        print("\nRespuesta de la API:")
        print("\nURL Imagen: " + image_url)
        print(f"Status code: {response.status_code}")
        print(f"Contenido: {response.text}")
        
        return "OK" in response.text  # CallMeBot responde "OK" cuando tiene éxito
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/trigger")
def check_and_send():
    today = datetime.now().strftime("%m-%d")
    print(f"Hoy es: {today}")
    
    sheet_url = "https://docs.google.com/spreadsheets/d/1Yd5BswTTYS9ClbMrDzcreHSDjs8Y8Onmz-otpDxksNk/export?format=csv"
    
    records = get_public_sheet_data(sheet_url)
    if not records:
        return {"status": "error", "message": "No hay datos en la hoja"}
    
    any_sent = False  # Bandera para verificar si hubo envíos
    
    for row in records:
        fecha_nacimiento = row.get("Fecha de nacimiento")
        if fecha_nacimiento:
            parts = fecha_nacimiento.split("-")
            if len(parts) >= 3:
                formatted_date = f"{parts[1]}-{parts[2]}"
                print(formatted_date)
                if formatted_date == today:
                    image_url = row.get("Imagen")
                    name = row.get('Nombre')
                    phone = row.get("Telefono")
                    cc = row.get("CC")
                    folder_url = "https://drive.google.com/drive/folders/1crBrwrLqyH67KFrWRGSldxDUuTvUs841"
                    target_file = f"{cc}.png"  # Nombre exacto del archivo que aparece en el HTML

                    id_file, resultados = buscar_archivo_en_drive(folder_url, target_file)
                    url_image = f"https://drive.google.com/uc?export=download&id={id_file}"
                    if image_url and name and phone:
                        try:
                            send_whatsapp_image(url_image, name, phone)
                            any_sent = True  # Marcamos que hubo al menos un envío
                            time.sleep(7)
                        except Exception as e:
                            print(f"Error al enviar a {name}: {str(e)}")
                    else:
                        print(f"Faltan datos (imagen, nombre o teléfono) para {name}")
            else:
                print("Formato de fecha inválido")
        else:
            print("Fecha de nacimiento no encontrada")
    
    if any_sent:
        return {
            "status": "success",
            "message": "Mensajes enviados a los cumpleañeros",
            "timestamp": datetime.now().isoformat()
        }
    else:
        return {
            "status": "skip",
            "message": "No hay cumpleaños hoy",
            "timestamp": datetime.now().isoformat()
        }
    #except Exception as e:
    #    return {"status": "error", "message": str(e)}


@app.get("/health")
def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "service": "Public Sheet WhatsApp Sender"
    }