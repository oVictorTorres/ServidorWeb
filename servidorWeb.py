import socket
import threading
import os
import mimetypes
import datetime

# --- Configuração do Servidor ---
WEB_ROOT = 'wwwroot'
HOST = '127.0.0.1'
PORT = 8080
LOG_FILE = 'server_log.txt'
LOG_LOCK = threading.Lock

# Mapeamento de extensões de arquivo para Content-Type.
mimetypes.init()

def log_request(client_addr, method, path, version, status_code, response_size, content_type, user_agent):
    """
    Registra os detalhes de uma requisição em um arquivo de log.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"[{timestamp}] - Cliente: {client_addr[0]}:{client_addr[1]} | "
        f"Requisição: {method} {path} {version} | "
        f"Status: {status_code} | Tamanho: {response_size} bytes | "
        f"Content-Type: {content_type} | User-Agent: {user_agent}\n"
    )
    
    with LOG_LOCK:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)


def send_error_response(conn, addr, method, path, version, status_code, message, user_agent='N/A'):
    """
    Envia uma resposta de erro HTTP com uma página HTML personalizada e registra o evento.
    """
    response_line = f"HTTP/1.1 {status_code} {message}\r\n"
    html_content = f"""
    <html>
    <head>
        <title>{status_code} {message}</title>
    </head>
    <body>
        <h1>{status_code} {message}</h1>
        <p>A requisição não pôde ser processada.</p>
    </body>
    </html>
    """
    html_content_bytes = html_content.encode('utf-8')
    headers = f"Content-Type: text/html\r\nContent-Length: {len(html_content_bytes)}\r\n\r\n"
    response = (response_line + headers).encode('utf-8') + html_content_bytes
    
    try:
        conn.sendall(response)
    except Exception as e:
        print(f"Erro ao enviar resposta de erro para {addr}: {e}")
    
    # Registra o erro no log
    log_request(addr, method, path, version, status_code, len(html_content_bytes), 'text/html', user_agent)


def generate_directory_listing(conn, addr, path, full_path, method, version, user_agent):
    """
    Gera dinamicamente uma página HTML listando os arquivos e diretórios e registra o evento.
    """
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Index of {path}</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: monospace; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <h1>Index of {path}</h1>
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Tamanho</th>
                        <th>Última Modificação</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        if path != '/':
            parent_path = os.path.dirname(path.rstrip('/'))
            if parent_path != '/':
                parent_path += '/'
            html_content += f'<tr><td><a href="{parent_path}">..</a></td><td>-</td><td>-</td></tr>'

        for item in sorted(os.listdir(full_path)):
            item_full_path = os.path.join(full_path, item)
            item_path = os.path.join(path, item) if not path.endswith('/') else path + item
            
            is_dir = os.path.isdir(item_full_path)
            
            size = '-'
            if not is_dir:
                try:
                    size = os.path.getsize(item_full_path)
                except OSError:
                    size = '-'
            
            try:
                mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(item_full_path)).strftime('%Y-%m-%d %H:%M:%S')
            except OSError:
                mod_time = '-'

            item_name = f'<b>{item}/</b>' if is_dir else item
            item_link = f"{item_path}/" if is_dir else item_path
            
            html_content += f'<tr><td><a href="{item_link}">{item_name}</a></td><td>{size}</td><td>{mod_time}</td></tr>'

        html_content += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        html_content_bytes = html_content.encode('utf-8')
        response_line = "HTTP/1.1 200 OK\r\n"
        headers = f"Content-Type: text/html; charset=utf-8\r\nContent-Length: {len(html_content_bytes)}\r\n\r\n"
        response_header = (response_line + headers).encode('utf-8')
        conn.sendall(response_header + html_content_bytes)
        
        # Registra a requisição no log
        log_request(addr, method, path, version, 200, len(html_content_bytes), 'text/html', user_agent)
    
    except Exception as e:
        print(f"Erro ao gerar listagem de diretório {path}: {e}")
        send_error_response(conn, addr, method, path, version, 500, "Internal Server Error", user_agent)


# --- Lógica de Processamento de Clientes ---

def handle_client(conn, addr):
    """
    Processa a requisição HTTP de um cliente e envia a resposta apropriada.
    """
    print(f"Iniciando thread para o cliente: {addr}")
    method, path, version, user_agent = 'N/A', 'N/A', 'N/A', 'N/A'
    try:
        with conn:
            request_data = conn.recv(4096)
            if not request_data:
                return

            request_string = request_data.decode('utf-8')
            lines = request_string.split('\n')
            request_line = lines[0].strip()
            parts = request_line.split(' ')

            if len(parts) != 3:
                send_error_response(conn, addr, method, path, version, 400, "Bad Request", user_agent)
                return

            method, path, version = parts
            
            for line in lines:
                if 'User-Agent:' in line:
                    user_agent = line.split('User-Agent:')[1].strip()
                    break

            if version != 'HTTP/1.1':
                send_error_response(conn, addr, method, path, version, 505, "HTTP Version Not Supported", user_agent)
                return

            if method != 'GET':
                send_error_response(conn, addr, method, path, version, 400, "Bad Request", user_agent)
                return

            # Normaliza o caminho
            if path == '/':
                path = '/index.html'

            full_path = os.path.join(WEB_ROOT, path.lstrip('/'))
            full_path = os.path.normpath(full_path) # Resolve '..' e outros

            # Verificação de segurança: não permitir sair do WEB_ROOT
            if not full_path.startswith(os.path.abspath(WEB_ROOT)):
                send_error_response(conn, addr, method, path, version, 400, "Bad Request", user_agent)
                return

            if not os.path.exists(full_path):
                send_error_response(conn, addr, method, path, version, 404, "Not Found", user_agent)
                return
            
            # Se for um diretório, verifica por index.html/htm ou gera listagem
            if os.path.isdir(full_path):
                index_path_html = os.path.join(full_path, 'index.html')
                index_path_htm = os.path.join(full_path, 'index.htm')
                
                if os.path.exists(index_path_html):
                    full_path = index_path_html
                elif os.path.exists(index_path_htm):
                    full_path = index_path_htm
                else:
                    # Garante que o caminho para o diretório termine com /
                    if not path.endswith('/'):
                        path += '/'
                    generate_directory_listing(conn, addr, path, full_path, method, version, user_agent)
                    return
            
            # Se for um arquivo, serve o arquivo
            if os.path.isfile(full_path):
                try:
                    content_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'
                    file_size = os.path.getsize(full_path)
                    
                    response_line = "HTTP/1.1 200 OK\r\n"
                    headers = f"Content-Type: {content_type}\r\nContent-Length: {file_size}\r\n\r\n"
                    response_header = (response_line + headers).encode('utf-8')
                    conn.sendall(response_header)
                    
                    with open(full_path, 'rb') as f:
                        chunk = f.read(4096)
                        while chunk:
                            conn.sendall(chunk)
                            chunk = f.read(4096)
                    
                    # Registra a requisição no log
                    log_request(addr, method, path, version, 200, file_size, content_type, user_agent)
                    print(f"Arquivo {full_path} enviado com sucesso para {addr}.")

                except FileNotFoundError:
                    send_error_response(conn, addr, method, path, version, 404, "Not Found", user_agent)
                except Exception as e:
                    print(f"Erro ao servir o arquivo: {e}")
                    send_error_response(conn, addr, method, path, version, 500, "Internal Server Error", user_agent)
            
    except socket.timeout:
        log_request(addr, method, path, version, 408, 0, 'N/A', user_agent)
    except Exception as e:
        print(f"Erro ao processar a requisição do cliente {addr}: {e}")
        send_error_response(conn, addr, method, path, version, 500, "Internal Server Error", user_agent)
            
    print(f"Fechando conexão com o cliente: {addr}")


# --- Início do Servidor ---

# Cria o diretório base se não existir
if not os.path.exists(WEB_ROOT):
    print(f"Criando diretório base para o servidor: {WEB_ROOT}")
    os.makedirs(WEB_ROOT)

try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Permite reutilizar o endereço
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Servidor escutando em {HOST}:{PORT}")

        while True:
            conn, addr = server_socket.accept()
            conn.settimeout(60) # Timeout para conexões
            
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

except KeyboardInterrupt:
    print("\nServidor encerrado por interrupção do usuário.")
except Exception as e:
    print(f"\nOcorreu um erro no servidor: {e}")