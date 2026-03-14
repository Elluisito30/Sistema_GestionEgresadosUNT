"""
Módulo de validación de datos para el sistema.
Proporciona funciones para validar diferentes tipos de entrada.
"""
import re
from datetime import datetime, date
from email_validator import validate_email, EmailNotValidError

def validar_dni(dni):
    """
    Valida un DNI peruano (8 dígitos).
    
    Args:
        dni (str): Número de DNI a validar
    
    Returns:
        tuple: (bool, str) - (válido, mensaje de error)
    """
    if not dni:
        return False, "El DNI es requerido"
    
    # Limpiar el DNI (quitar espacios y guiones)
    dni_limpio = re.sub(r'[\s-]', '', str(dni))
    
    if not dni_limpio.isdigit():
        return False, "El DNI debe contener solo números"
    
    if len(dni_limpio) != 8:
        return False, "El DNI debe tener 8 dígitos"
    
    # Validación adicional: dígito de verificación (opcional)
    # Aquí se podría implementar la validación del dígito verificador del RENIEC
    
    return True, dni_limpio

def validar_ruc(ruc):
    """
    Valida un RUC peruano (11 dígitos).
    
    Args:
        ruc (str): Número de RUC a validar
    
    Returns:
        tuple: (bool, str) - (válido, mensaje de error)
    """
    if not ruc:
        return False, "El RUC es requerido"
    
    # Limpiar el RUC
    ruc_limpio = re.sub(r'[\s-]', '', str(ruc))
    
    if not ruc_limpio.isdigit():
        return False, "El RUC debe contener solo números"
    
    if len(ruc_limpio) != 11:
        return False, "El RUC debe tener 11 dígitos"
    
    # Validación del dígito verificador (algoritmo de SUNAT)
    # Los primeros dos dígitos: 10 (persona natural), 20 (empresa), etc.
    primeros_dos = int(ruc_limpio[:2])
    if primeros_dos not in [10, 15, 17, 20]:
        return False, "Los primeros dígitos del RUC no son válidos"
    
    # Calcular dígito verificador (algoritmo módulo 11)
    factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = 0
    for i in range(10):
        suma += int(ruc_limpio[i]) * factores[i]
    
    residuo = suma % 11
    digito_verificador = 11 - residuo
    if digito_verificador == 11:
        digito_verificador = 0
    elif digito_verificador == 10:
        digito_verificador = 1
    
    if digito_verificador != int(ruc_limpio[10]):
        return False, "El RUC no es válido (dígito verificador incorrecto)"
    
    return True, ruc_limpio

def validar_email(email, dominio_institucional=None):
    """
    Valida un email y opcionalmente verifica que sea de un dominio específico.
    
    Args:
        email (str): Email a validar
        dominio_institucional (str, optional): Dominio requerido (ej. 'unitru.edu.pe')
    
    Returns:
        tuple: (bool, str) - (válido, mensaje de error)
    """
    if not email:
        return False, "El email es requerido"
    
    try:
        # Validación de formato usando la librería email-validator
        validation = validate_email(email, check_deliverability=False)
        email_validado = validation.email
        
        # Validación de dominio institucional si se requiere
        if dominio_institucional:
            if not email_validado.endswith(f'@{dominio_institucional}'):
                return False, f"El email debe ser del dominio @{dominio_institucional}"
        
        return True, email_validado
        
    except EmailNotValidError as e:
        return False, str(e)

def validar_telefono(telefono):
    """
    Valida un número de teléfono peruano.
    
    Args:
        telefono (str): Número de teléfono
    
    Returns:
        tuple: (bool, str) - (válido, mensaje de error)
    """
    if not telefono:
        return True, ""  # Teléfono es opcional
    
    # Limpiar el teléfono
    tel_limpio = re.sub(r'[\s\-\(\)]', '', str(telefono))
    
    if not tel_limpio.isdigit():
        return False, "El teléfono debe contener solo números"
    
    # Validar longitud (9 para celular, 7 para fijo)
    if len(tel_limpio) not in [7, 9]:
        return False, "El teléfono debe tener 7 o 9 dígitos"
    
    # Validar que empiece con 9 si es celular
    if len(tel_limpio) == 9 and not tel_limpio.startswith('9'):
        return False, "Los celulares deben comenzar con 9"
    
    return True, tel_limpio

def validar_fecha(fecha_str, formato='%Y-%m-%d', min_fecha=None, max_fecha=None):
    """
    Valida una fecha en formato string.
    
    Args:
        fecha_str (str): Fecha a validar
        formato (str): Formato esperado de la fecha
        min_fecha (date, optional): Fecha mínima permitida
        max_fecha (date, optional): Fecha máxima permitida
    
    Returns:
        tuple: (bool, date/str) - (válido, fecha validada o mensaje de error)
    """
    if not fecha_str:
        return False, "La fecha es requerida"
    
    try:
        fecha = datetime.strptime(fecha_str, formato).date()
        
        if min_fecha and fecha < min_fecha:
            return False, f"La fecha no puede ser anterior a {min_fecha.strftime('%d/%m/%Y')}"
        
        if max_fecha and fecha > max_fecha:
            return False, f"La fecha no puede ser posterior a {max_fecha.strftime('%d/%m/%Y')}"
        
        return True, fecha
        
    except ValueError:
        return False, f"Formato de fecha inválido. Use {formato}"

def validar_rango_salario(min_salario, max_salario):
    """
    Valida un rango salarial.
    
    Args:
        min_salario (float): Salario mínimo
        max_salario (float): Salario máximo
    
    Returns:
        tuple: (bool, str) - (válido, mensaje de error)
    """
    if min_salario and max_salario:
        if min_salario > max_salario:
            return False, "El salario mínimo no puede ser mayor al máximo"
        
        if min_salario < 0 or max_salario < 0:
            return False, "Los salarios no pueden ser negativos"
    
    return True, ""

def validar_requerido(valor, nombre_campo):
    """
    Valida que un campo requerido no esté vacío.
    
    Args:
        valor: Valor a validar
        nombre_campo (str): Nombre del campo para el mensaje
    
    Returns:
        tuple: (bool, str) - (válido, mensaje de error)
    """
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return False, f"{nombre_campo} es requerido"
    
    return True, valor

def sanitizar_entrada(texto):
    """
    Sanitiza texto de entrada para prevenir XSS.
    
    Args:
        texto (str): Texto a sanitizar
    
    Returns:
        str: Texto sanitizado
    """
    if not texto:
        return ""
    
    # Reemplazar caracteres peligrosos
    texto = str(texto)
    texto = texto.replace('<', '&lt;')
    texto = texto.replace('>', '&gt;')
    texto = texto.replace('"', '&quot;')
    texto = texto.replace("'", '&#x27;')
    texto = texto.replace('/', '&#x2F;')
    
    return texto.strip()