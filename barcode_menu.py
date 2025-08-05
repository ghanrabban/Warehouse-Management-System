import os
import sys
import random
import serial
import serial.tools.list_ports
from barcode import get_barcode_class
import mysql.connector

# Database connection settings for Docker MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASS', 'secret'),
    'database': os.getenv('DB_NAME', 'wms_demo')
}

# Initialize dummy table
def init_db():
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']};")
    cursor.execute(f"USE {DB_CONFIG['database']};")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scanned_barcodes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(128) NOT NULL,
            source ENUM('scan','generate','manual') NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    cursor.close()
    conn.close()

# Save barcode event
def save_barcode_event(code, source):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f"USE {DB_CONFIG['database']};")
    cursor.execute(
        "INSERT INTO scanned_barcodes (code, source) VALUES (%s, %s)",
        (code, source)
    )
    conn.commit()
    cursor.close()
    conn.close()


def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        raise RuntimeError("No serial ports found.")
    return ports[-1].device


def scan_loop():
    try:
        device = list_serial_ports()
        ser = serial.Serial(device, baudrate=9600, timeout=1)
        print(f"Connected to scanner on {device}")
    except Exception as e:
        print(f"Error opening scanner port: {e}")
        return

    buffer = ''
    print("Start scanning barcodes (Ctrl+C to stop):")
    try:
        while True:
            byte = ser.read()
            if not byte:
                continue
            if byte == b'\r':
                code = buffer.strip()
                if code:
                    print(f"Scanned barcode: {code}")
                    save_barcode_event(code, 'scan')
                buffer = ''
            else:
                buffer += byte.decode('utf-8', errors='ignore')
    except KeyboardInterrupt:
        print("\nStopping scan loop.")
    finally:
        ser.close()


def generate_barcode():
    print("\nChoose barcode type:")
    print("1. EAN-13")
    print("2. Code128")
    btype = input("Select type [1-2]: ").strip()

    if btype == '1':
        data = input("Enter 12-digit EAN data (leave blank for random): ").strip()
        if not data:
            data = ''.join(str(random.randint(0, 9)) for _ in range(12))
            print(f"Generated random data: {data}")
        if not data.isdigit() or len(data) != 12:
            print("Invalid data: must be exactly 12 digits for EAN-13")
            return
        barcode_class = get_barcode_class('ean13')
    elif btype == '2':
        data = input("Enter data for Code128 (leave blank for random 10-chars): ").strip()
        if not data:
            data = ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=10))
            print(f"Generated random data: {data}")
        barcode_class = get_barcode_class('code128')
    else:
        print("Invalid selection.")
        return

    fmt = input("Select output format [png/svg] (default png): ").strip().lower() or 'png'
    writer = None
    if fmt == 'png':
        try:
            from barcode.writer import ImageWriter
            writer = ImageWriter()
        except ImportError:
            print("Pillow not installed; falling back to SVG format.")
            writer = None

    output = input("Enter output filename (without extension): ").strip() or 'barcode'
    try:
        print(f"Generating a barcode using {barcode_class.name.upper()} in {fmt.upper()} format...")
        barcode_obj = barcode_class(data, writer=writer)
        filename = barcode_obj.save(output)
        ext = '.png' if writer else '.svg'
        print(f"Barcode generated and saved to {filename + ext}")
        save_barcode_event(data, 'generate')
    except Exception as e:
        print(f"Error generating barcode: {e}")


def manual_input():
    print("\nManual barcode entry (leave blank to return to menu)")
    while True:
        code = input("Enter barcode number: ").strip()
        if not code:
            break
        print(f"Manual input barcode: {code}")
        save_barcode_event(code, 'manual')


def main_menu():
    print("Initializing database integration (Docker MySQL)...")
    init_db()

    while True:
        print("\n=== Barcode System Menu ===")
        print("1. Scan barcode")
        print("2. Generate barcode (EAN-13 / Code128)")
        print("3. Manual input barcode")
        print("4. Exit")
        choice = input("Select an option [1-4]: ").strip()

        if choice == '1':
            scan_loop()
        elif choice == '2':
            generate_barcode()
        elif choice == '3':
            manual_input()
        elif choice == '4':
            print("Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please choose 1, 2, 3, or 4.")


if __name__ == '__main__':
    main_menu()