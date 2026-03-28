#!/usr/bin/env python3
"""Generate a default product placeholder image using only stdlib."""
import struct, zlib, base64, os

def create_placeholder_png(width, height, r, g, b, text="🎁"):
    """Creates a minimal valid PNG with a solid color."""
    def chunk(name, data):
        c = struct.pack('>I', len(data)) + name + data
        crc = zlib.crc32(name + data) & 0xffffffff
        return c + struct.pack('>I', crc)
    
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    raw = b''
    for _ in range(height):
        raw += b'\x00'
        for _ in range(width):
            raw += bytes([r, g, b])
    
    idat = zlib.compress(raw)
    
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', ihdr)
    png += chunk(b'IDAT', idat)
    png += chunk(b'IEND', b'')
    return png

os.makedirs('static/images/uploads', exist_ok=True)
os.makedirs('static/images', exist_ok=True)

# Create default product placeholder
png_data = create_placeholder_png(400, 400, 242, 237, 232)
with open('static/images/default_product.png', 'wb') as f:
    f.write(png_data)

print("Default image created.")
