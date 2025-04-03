from fastapi import FastAPI, HTTPException
from datetime import datetime
import requests
import csv
from io import StringIO
from pydantic import BaseModel
from typing import Optional
import time
from bs4 import BeautifulSoup


app = FastAPI()


def buscar_archivo_en_drive(folder_url, target_file):
    folder_id = folder_url.split("/")[-1]
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None, []
    
    soup = BeautifulSoup(response.text, "html.parser")
    found_files = []
    
    # Find all file entries by their links
    for a_tag in soup.select("a"):
        href = a_tag.get("href", "")
        if "/file/d/" in href:
            # Extract file ID from the URL
            file_id = href.split("/file/d/")[1].split("/")[0]
            file_name = a_tag.text.strip()
            
            if target_file.lower() in file_name.lower():
                found_files.append({
                    "name": file_name,
                    "url": f"https://drive.google.com/uc?export=download&id={file_id}",
                    "id": file_id
                })
    
    # Return the first matching file (or None if none found)
    if found_files:
        return found_files[0]["id"], found_files
    else:
        return None, []

class WhatsAppResponse(BaseModel):
    status: str
    message: str
    image_url: Optional[str] = None
    timestamp: str

def get_public_sheet_data(sheet_url: str):
    try:
        response = requests.get(
            sheet_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            allow_redirects=True,
            timeout=10,
        )
        response.raise_for_status()
        
        # Usar response.content (bytes) y decodificar explícitamente con utf-8-sig
        csv_data = response.content.decode("utf-8-sig")
        return list(csv.DictReader(StringIO(csv_data)))
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sheet: {str(e)}")
        
#content = response.content.decode("utf-8-sig")
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
    
    any_sent = False
    
    for row in records:
        fecha_nacimiento = row.get("Fecha de nacimiento")
        if fecha_nacimiento:
            parts = fecha_nacimiento.split("-")
            if len(parts) >= 3:
                formatted_date = f"{parts[1]}-{parts[2]}"
                print(formatted_date)
                if formatted_date == today:
                    name = row.get('Nombre')
                    phone = row.get("Telefono")
                    cc = row.get("CC")
                    target_file = f"{cc}.png"  # Ejemplo: "1088312612.png"
                    print(target_file)
                    # Buscar el archivo en Drive
                    folder_url = "https://drive.google.com/drive/folders/1crBrwrLqyH67KFrWRGSldxDUuTvUs841"
                    file_id, _ = buscar_archivo_en_drive(folder_url, target_file)
                    
                    if file_id:
                        url_image = f"https://drive.google.com/uc?export=download&id={file_id}"
                        try:
                            send_whatsapp_image(url_image, name, phone)
                            any_sent = True
                            time.sleep(7)
                        except Exception as e:
                            print(f"Error al enviar a {name}: {str(e)}")
                    else:
                        print(f"No se encontró el archivo {target_file} para {name}")
                else:
                    print("Fecha no coincide")
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

@app.get("/health")
def health_check():
    return {
        "status": "OK",
        "timestamp": datetime.now().isoformat(),
        "service": "Public Sheet WhatsApp Sender"
    }