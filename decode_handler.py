#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ACARS Message Decoder Handler
Libacars kütüphanesini kullanarak ACARS mesajlarını decode eder
"""
import ctypes
import os
import logging
from ctypes import c_char_p, c_void_p, c_int, c_bool, POINTER, Structure

logger = logging.getLogger(__name__)


class DecodeHandler:
    """ACARS mesajlarını decode eden handler"""
    
    # Message direction enum
    LA_MSG_DIR_UNKNOWN = 0
    LA_MSG_DIR_GND2AIR = 1
    LA_MSG_DIR_AIR2GND = 2
    
    # Desteklenen ACARS label'ları (libacars tarafından decode edilebilen)
    # Kaynak: libacars/acars.c - la_acars_apps_parse_and_reassemble()
    SUPPORTED_LABELS = {
        # ARINC-622 FANS-1/A (CPDLC & ADS-C)
        'A6',  # ARINC-622 ADS-C
        'AA',  # ARINC-622 CPDLC
        'B6',  # ARINC-622 ADS-C
        'BA',  # ARINC-622 CPDLC
        
        # H1 - Multi-purpose (ARINC-622 / MIAM / OHMA - sublabel'a göre)
        'H1',  # FANS-1/A CPDLC/ADS-C, MIAM, OHMA
        
        # Media Advisory
        'SA',  # Media Advisory (VHF, HF, Satcom status)
        
        # MIAM (Media Independent Aircraft Messaging)
        'MA',  # MIAM
    }
    
    def __init__(self, lib_path=None):
        """
        Args:
            lib_path: libacars-2.dll'in tam yolu
        """
        self.lib = None
        self.initialized = False
        
        try:
            if lib_path is None:
                # DLL'i ana dizinde ara
                script_dir = os.path.dirname(os.path.abspath(__file__))
                lib_path = os.path.join(script_dir, 'libacars-2.dll')
                
                # Ana dizinde yoksa example decoding klasöründe ara
                if not os.path.exists(lib_path):
                    lib_path = os.path.join(script_dir, 'example decoding', 'libacars-2.dll')
            
            if not os.path.exists(lib_path):
                logger.warning(f"libacars DLL bulunamadı: {lib_path}. Decode özelliği devre dışı.")
                return
            
            # DLL'i yükle
            self.lib = ctypes.CDLL(lib_path)
            
            # la_proto_node yapısını tanımla (opaque pointer)
            self.la_proto_node_p = c_void_p
            
            # la_vstring yapısını tanımla
            class la_vstring(Structure):
                _fields_ = [
                    ("str", c_char_p),
                    ("len", ctypes.c_size_t),
                    ("allocated_size", ctypes.c_size_t)
                ]
            
            self.la_vstring = la_vstring
            self.la_vstring_p = POINTER(la_vstring)
            
            # Fonksiyon prototiplerini ayarla
            self.lib.la_acars_decode_apps.argtypes = [c_char_p, c_char_p, c_int]
            self.lib.la_acars_decode_apps.restype = self.la_proto_node_p
            
            self.lib.la_proto_tree_format_text.argtypes = [self.la_vstring_p, self.la_proto_node_p]
            self.lib.la_proto_tree_format_text.restype = self.la_vstring_p
            
            self.lib.la_proto_tree_destroy.argtypes = [self.la_proto_node_p]
            self.lib.la_proto_tree_destroy.restype = None
            
            self.lib.la_vstring_destroy.argtypes = [self.la_vstring_p, c_bool]
            self.lib.la_vstring_destroy.restype = None
            
            self.lib.la_acars_extract_sublabel_and_mfi.argtypes = [
                c_char_p, c_int, c_char_p, ctypes.c_size_t, c_char_p, c_char_p
            ]
            self.lib.la_acars_extract_sublabel_and_mfi.restype = c_int
            
            self.lib.la_config_set_bool.argtypes = [c_char_p, c_bool]
            self.lib.la_config_set_bool.restype = None
            
            # Prettify ayarları
            self.lib.la_config_set_bool(b"prettify_xml", True)
            self.lib.la_config_set_bool(b"prettify_json", True)
            
            self.initialized = True
            logger.info(f"DecodeHandler successfully loaded: {lib_path}")
            
        except Exception as e:
            logger.error(f"DecodeHandler failed to load: {e}")
            self.lib = None
            self.initialized = False
    
    def is_decodable(self, label):
        """
        Verilen label'ın decode edilebilir olup olmadığını kontrol et
        
        Args:
            label: ACARS label (2 karakter)
        
        Returns:
            bool: Label decode edilebilir mi?
        """
        if not self.initialized or not label:
            return False
        
        return label.upper() in self.SUPPORTED_LABELS
    
    def decode_message(self, label, message, direction='downlink'):
        """
        ACARS mesajını decode et
        
        Args:
            label: ACARS label (2 karakter)
            message: Mesaj içeriği
            direction: 'downlink' veya 'uplink'
        
        Returns:
            str or None: Decode edilmiş mesaj metni, decode edilemezse None
        """
        if not self.initialized:
            return None
        
        if not label or len(label) != 2:
            return None
        
        if not self.is_decodable(label):
            return None
        
        # Direction'ı enum'a çevir
        if direction.lower() in ['downlink', 'd', 'air2gnd']:
            msg_dir = self.LA_MSG_DIR_AIR2GND
        elif direction.lower() in ['uplink', 'u', 'gnd2air']:
            msg_dir = self.LA_MSG_DIR_GND2AIR
        else:
            msg_dir = self.LA_MSG_DIR_AIR2GND  # Default downlink
        
        try:
            # String'leri byte'a çevir
            label_bytes = label.upper().encode('utf-8')
            message_bytes = message.encode('utf-8')
            
            # Sublabel ve MFI'yi çıkar (H1 label için gerekli)
            sublabel_buf = ctypes.create_string_buffer(3)
            mfi_buf = ctypes.create_string_buffer(3)
            
            offset = self.lib.la_acars_extract_sublabel_and_mfi(
                label_bytes,
                msg_dir,
                message_bytes,
                len(message_bytes),
                sublabel_buf,
                mfi_buf
            )
            
            # Offset'ten sonraki mesaj kısmını kullan
            if offset > 0:
                decode_message = message_bytes[offset:]
            else:
                decode_message = message_bytes
            
            # ACARS application'ı decode et
            node = self.lib.la_acars_decode_apps(label_bytes, decode_message, msg_dir)
            
            if not node:
                return None
            
            try:
                # Protocol tree'yi text formatında al
                vstr_ptr = self.lib.la_proto_tree_format_text(None, node)
                
                if not vstr_ptr:
                    return None
                
                # vstring içeriğini oku
                vstr = vstr_ptr.contents
                decoded_text = vstr.str.decode('utf-8') if vstr.str else None
                
                # Belleği temizle
                self.lib.la_vstring_destroy(vstr_ptr, True)
                
                return decoded_text
                
            finally:
                # Protocol tree'yi temizle
                self.lib.la_proto_tree_destroy(node)
                
        except Exception as e:
            logger.error(f"Decode error (label={label}): {e}")
            return None
    
    def process_message(self, message_data):
        """
        Mesaj verisini işle ve decode edilmişse decoded field ekle
        
        Args:
            message_data: Mesaj verisi dict (label ve text içermeli)
        
        Returns:
            dict: İşlenmiş mesaj verisi (decoded field eklenmiş olabilir)
        """
        if not self.initialized:
            return message_data
        
        label = message_data.get('label', '')
        text = message_data.get('text', '')
        
        if not label or not text:
            return message_data
        
        # Label decode edilebilir mi kontrol et
        if self.is_decodable(label):
            decoded = self.decode_message(label, text)
            if decoded:
                message_data['decoded'] = decoded
                logger.debug(f"Message decoded: label={label}")
        
        return message_data
