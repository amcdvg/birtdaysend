import requests
from bs4 import BeautifulSoup

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

# Ejemplo de uso
folder_url = "https://drive.google.com/drive/folders/1crBrwrLqyH67KFrWRGSldxDUuTvUs841"
target_file = "1088312612.png"  # Nombre exacto del archivo que aparece en el HTML

resultados = buscar_archivo_en_drive(folder_url, target_file)
#https://drive.google.com/file/d/17JGhpkb2_0s4yNMyhEXZWbs5ekEQwhyZ/view?usp=drive_link
if not resultados:
    print("Archivo no encontrado.")
else:
    for file in resultados:
        print(f"Nombre: {file['name']}")
        print(f"Enlace: {file['url']}\n")