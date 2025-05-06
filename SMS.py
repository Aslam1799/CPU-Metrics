import smtplib
import psutil
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def setup_server():
    server = smtplib.SMTP(host="smtp.gmail.com", port=587)
    server.starttls()
    return server

def login(server):
    address = input("Sender Email: ").strip()
    password = input("Password: ").strip()
    server.login(address, password)
    return address

def get_system_metrics():
    metrics = []

    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    metrics.append(f"CPU Usage: {cpu_percent}%")

    # Memory usage
    mem = psutil.virtual_memory()
    metrics.append(f"Memory Usage: {mem.percent}% ({mem.used // (1024 ** 2)}MB used of {mem.total // (1024 ** 2)}MB)")

    # Disk usage
    disk = psutil.disk_usage('/')
    metrics.append(f"Disk Usage: {disk.percent}% ({disk.used // (1024 ** 3)}GB used of {disk.total // (1024 ** 3)}GB)")

    # Top 5 processes by CPU usage
    processes = sorted(psutil.process_iter(['pid', 'name', 'cpu_percent']), key=lambda p: p.info['cpu_percent'], reverse=True)
    metrics.append("\nTop 5 CPU-Intensive Processes:")
    for proc in processes[:5]:
        metrics.append(f"PID {proc.info['pid']} - {proc.info['name']} - {proc.info['cpu_percent']}% CPU")

    # Top 5 processes by number of network connections
    metrics.append("\n=== Top 5 Processes by Network Connections ===")
    conn_map = {}
    for conn in psutil.net_connections(kind='inet'):
        if conn.pid is not None:
            conn_map[conn.pid] = conn_map.get(conn.pid, 0) + 1

    proc_conn_info = []
    for pid, count in conn_map.items():
        try:
          name = psutil.Process(pid).name()
          proc_conn_info.append((pid, name, count))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    top_network = sorted(proc_conn_info, key=lambda x: x[2], reverse=True)[:5]
    for pid, name, conn_count in top_network:
        metrics.append(f"PID {pid} - {name} - {conn_count} connections")

    return "\n".join(metrics)

def add_attachment(msg):
    filename = input("Enter path of the attachment file: ").strip()
    try:
        with open(filename, 'rb') as file:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(file.read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', f'attachment; filename="{filename.split("/")[-1]}"')
            msg.attach(attachment)
            print("Attachment added.")
    except FileNotFoundError:
        print("File not found. Skipping attachment.")

def create_email(address):
    recipient_email = input("Enter recipient email: ").strip()
    subject = input("Enter subject of the message: ").strip()

    msg = MIMEMultipart()
    msg['From'] = address
    msg['To'] = recipient_email
    msg['Subject'] = subject

    system_metrics = get_system_metrics()
    msg.attach(MIMEText(system_metrics, 'plain'))

    attach = input("Would you like to send an attachment? Yes/No: ").strip().lower()
    if attach == 'yes':
        try:
            num_attach = int(input("Enter number of attachments: "))
            for _ in range(num_attach):
                add_attachment(msg)
        except ValueError:
            print("Invalid number. Skipping attachments.")
    return msg

def send(server, msg):
    server.send_message(msg)
    print("Email sent successfully.")
    del msg


# === Main Execution ===
server = setup_server()
address = login(server)
msg = create_email(address)
send(server, msg)
server.quit()
# === End of Script ===