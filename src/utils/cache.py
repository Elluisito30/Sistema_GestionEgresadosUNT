"""
Sistema de caché para mejorar el rendimiento.
"""
import streamlit as st
from functools import wraps
from datetime import datetime, timedelta
from typing import Any, Callable, Optional
import hashlib
import json

class CacheManager:
    """Gestor de caché para la aplicación."""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene un valor del caché."""
        if key in self._cache:
            # Verificar si ha expirado
            if key in self._timestamps:
                timestamp, ttl = self._timestamps[key]
                if datetime.now() - timestamp > timedelta(seconds=ttl):
                    self.delete(key)
                    return default
            return self._cache[key]
        return default
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """
        Guarda un valor en el caché.
        
        Args:
            key: Clave del caché
            value: Valor a guardar
            ttl: Tiempo de vida en segundos (default: 5 minutos)
        """
        self._cache[key] = value
        self._timestamps[key] = (datetime.now(), ttl)
    
    def delete(self, key: str):
        """Elimina un valor del caché."""
        if key in self._cache:
            del self._cache[key]
        if key in self._timestamps:
            del self._timestamps[key]
    
    def clear(self):
        """Limpia todo el caché."""
        self._cache.clear()
        self._timestamps.clear()
    
    def generate_key(self, *args, **kwargs) -> str:
        """
        Genera una clave única basada en argumentos.
        """
        key_parts = []
        
        for arg in args:
            key_parts.append(str(arg))
        
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

# Instancia global de caché
_cache_manager = CacheManager()

def cached(ttl: int = 300):
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        ttl: Tiempo de vida en segundos
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de caché
            key = _cache_manager.generate_key(func.__name__, *args, **kwargs)
            
            # Intentar obtener del caché
            cached_result = _cache_manager.get(key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y guardar en caché
            result = func(*args, **kwargs)
            _cache_manager.set(key, result, ttl)
            
            return result
        return wrapper
    return decorator

# Decoradores específicos para Streamlit
def st_cached_data(ttl: int = 3600):
    """
    Decorador para cachear datos en Streamlit.
    Combina el caché de Streamlit con el nuestro.
    """
    def decorator(func: Callable):
        @wraps(func)
        @st.cache_data(ttl=ttl)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

def st_cached_resource(ttl: int = 3600):
    """
    Decorador para cachear recursos en Streamlit.
    """
    def decorator(func: Callable):
        @wraps(func)
        @st.cache_resource(ttl=ttl)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Funciones de utilidad para caché
def invalidate_cache(pattern: Optional[str] = None):
    """
    Invalida entradas del caché que coincidan con un patrón.
    
    Args:
        pattern: Patrón para filtrar claves (None para limpiar todo)
    """
    if pattern is None:
        _cache_manager.clear()
    else:
        keys_to_delete = [k for k in _cache_manager._cache.keys() if pattern in k]
        for key in keys_to_delete:
            _cache_manager.delete(key)