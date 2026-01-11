from pathlib import Path
import sys
import os
import time
import io
import hashlib
from PIL import Image, ImageGrab
import tkinter as tk

#!/usr/bin/env python3
# save_cover.py
# Espera continuamente imágenes pegadas en el portapapeles, las redimensiona a 500x500 y las guarda en covers/default como .jpg

def compute_fingerprint_from_clipboard_raw(raw):
    if raw is None:
        return None
    # Si clipboard devuelve rutas de archivos, usar la primera ruta como huella
    if isinstance(raw, (list, tuple)) and raw:
        try:
            return f"FILE:{str(Path(raw[0]).resolve())}"
        except Exception:
            return None
    # Si es una imagen PIL u objeto similar, guardar en bytes y hashear
    try:
        if hasattr(raw, "tobytes") or hasattr(raw, "save"):
            buf = io.BytesIO()
            # intentar salvar como PNG para estabilidad
            try:
                raw.save(buf, format="PNG")
            except Exception:
                # si no tiene save, intentar obtener de ImageGrab retorno directo
                # convertir a PIL.Image si tiene resize
                if hasattr(raw, "resize"):
                    raw = raw
                else:
                    return None
                raw.save(buf, format="PNG")
            h = hashlib.md5(buf.getvalue()).hexdigest()
            return f"IMG:{h}"
    except Exception:
        return None
    return None

def get_image_from_clipboard():
    raw = ImageGrab.grabclipboard()
    if raw is None:
        return None, None
    # Si clipboard devuelve rutas de archivos, abrir la primera
    if isinstance(raw, (list, tuple)) and raw:
        try:
            img = Image.open(raw[0])
            fp = compute_fingerprint_from_clipboard_raw(raw)
            return img, fp
        except Exception:
            return None, None
    # Si ya es una Image o similar
    try:
        if hasattr(raw, "resize") or hasattr(raw, "save"):
            fp = compute_fingerprint_from_clipboard_raw(raw)
            return raw, fp
    except Exception:
        pass
    return None, None


def get_clipboard_text():
    """Intentar obtener texto del portapapeles usando tkinter.
    Devuelve None si no hay texto o ocurre un error.
    """
    try:
        root = tk.Tk()
        root.withdraw()
        try:
            text = root.clipboard_get()
        except Exception:
            text = None
        root.destroy()
        return text
    except Exception:
        return None

def sanitize_name(name: str) -> str:
    # quitar espacios al inicio/fin, quitar extensión si la puso, y caracteres no permitidos
    name = os.path.basename(name).strip()
    if name.lower().endswith(".jpg") or name.lower().endswith(".jpeg"):
        name = ".".join(name.split(".")[:-1])
    # reemplazar caracteres peligrosos por guion bajo
    return "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in name).strip() or "cover"

def main():
    script_dir = Path(__file__).resolve().parent
    covers_dir = script_dir.parent / "covers" / "default"
    covers_dir.mkdir(parents=True, exist_ok=True)

    last_fp = None
    print("Esperando imágenes en el portapapeles. Presiona Ctrl+C para salir.")
    try:
        while True:
            img, fp = get_image_from_clipboard()
            if img is None or fp is None:
                time.sleep(0.5)
                continue
            # si la huella es igual a la anterior, esperar a cambio
            if fp == last_fp:
                time.sleep(0.5)
                continue

            last_fp = fp
            print("Imagen detectada en el portapapeles.")

            # Esperar nombre en el portapapeles: debe contener '-' para ser válido.
            print("Esperando nombre en el portapapeles (debe contener '-')...")
            name = None
            while True:
                text = get_clipboard_text()
                if text:
                    # quitar espacios y saltos de linea
                    cleaned = "".join(text.split())
                    if "-" in cleaned:
                        name = sanitize_name(cleaned)
                        break
                time.sleep(0.5)

            out_path = covers_dir / f"{name}.jpg"

            # Asegurar modo RGB (JPEG no soporta transparencia)
            try:
                img_converted = img.convert("RGB")
                img_resized = img_converted.resize((500, 500), Image.LANCZOS)
                img_resized.save(out_path, format="JPEG", quality=95)
            except Exception as e:
                print("Error al procesar o guardar la imagen:", e)
                # no salir del loop, seguir esperando nuevas imágenes
                continue

            print(f"Imagen guardada en: {out_path}")
            # después de guardar, esperar un momento antes de seguir para evitar doble captura
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nSaliendo.")
        sys.exit(0)

if __name__ == "__main__":
    main()