# Projeto 2 - Servidor Web (HTTP/1.1)

Este é um projeto para a disciplina de **Redes de Computadores** do curso de Bacharelado em Engenharia da Computação da **Universidade Federal Rural de Pernambuco (UFRPE) - UABJ**.

O objetivo foi desenvolver um servidor web HTTP/1.1 do zero em Python, utilizando apenas a biblioteca de `sockets`. O projeto **não utiliza** frameworks ou bibliotecas que abstraem o protocolo (como Flask ou Django), focando na implementação manual do protocolo e no controle de conexões.

## ✨ Funcionalidades Implementadas

O servidor atende a todos os requisitos do projeto, incluindo:

* **Protocolo HTTP/1.1:** Implementação do protocolo com suporte exclusivo ao método `GET`.
* **Concorrência:** O servidor é **multithread**, capaz de atender múltiplos clientes simultaneamente.
* **Códigos de Status:** Responde adequadamente com todos os códigos de status solicitados:
    * **`200 OK`**: Para requisições bem-sucedidas.
    * **`400 Bad Request`**: Para requisições mal formatadas ou métodos não suportados.
    * **`404 Not Found`**: Para arquivos ou diretórios não encontrados.
    * **`505 HTTP Version Not Supported`**: Para requisições com versões HTTP diferentes de 1.1.
* **Páginas de Erro:** Retorna páginas HTML personalizadas para todos os códigos de erro.
* **Serviço de Arquivos:** Envia arquivos de diversos tipos (texto e binário), como `.html`, `.css`, `.jpg` e `.iso`/`.wsl`.
* **Leitura Preguiçosa:** Utiliza leitura em *chunks* (lazy evaluation) para enviar arquivos grandes (como .iso) sem sobrecarregar a memória RAM.
* **Listagem de Diretórios:** Gera dinamicamente uma página HTML navegável caso um diretório sem `index.html` ou `index.htm` seja requisitado.
* **Logs de Auditoria:** Registra todas as requisições (com data, IP, método, status, tamanho, User-Agent, etc.) em um arquivo `server_log.txt`.
* **Pasta Raiz:** Opera sobre uma pasta base (`wwwroot`) que é criada automaticamente se não existir.

## 🛠️ Tecnologias Utilizadas

* **Python 3.10**
* Bibliotecas Nativas:
    * `socket` (Para comunicação TCP)
    * `threading` (Para concorrência)
    * `os` (Para manipulação do sistema de arquivos)
    * `mimetypes` (Para identificar Content-Type)
    * `datetime` (Para os logs)

## 🚀 Como Executar

Este projeto não requer instalação de dependências externas.

### Pré-requisitos

* Python 3.x

### Passos

1.  Clone este repositório:
    ```bash
    git clone <url-do-seu-repositorio>
    ```
2.  Navegue até a pasta do projeto:
    ```bash
    cd <nome-da-pasta-do-projeto>
    ```
3.  Execute o servidor:
    ```bash
    python servidorWeb.py
    ```
4.  O servidor será iniciado e criará automaticamente a pasta `wwwroot`. A mensagem `Servidor escutando em 127.0.0.1:8080` aparecerá no terminal.

## 🧪 Como Testar

Após iniciar o servidor, você pode testar as funcionalidades:

1.  **Página Principal (200 OK):**
    * Adicione o arquivo `index.html` (fornecido no projeto) à pasta `wwwroot`.
    * Acesse no navegador: `http://127.0.0.1:8080`

2.  **Listagem de Diretório:**
    * Crie uma subpasta dentro de `wwwroot` (ex: `wwwroot/imagens`).
    * Coloque arquivos dentro dela.
    * Acesse: `http://127.0.0.1:8080/imagens/`

3.  **Download de Arquivo (Binário):**
    * Coloque um arquivo grande (ex: `ubuntu.wsl`) dentro da `wwwroot`.
    * Acesse: `http://127.0.0.1:8080/ubuntu.wsl` (O download iniciará).

4.  **Erro (404 Not Found):**
    * Tente acessar um arquivo que não existe:
    * Acesse: `http://127.0.0.1:8080/pagina-que-nao-existe.html`

5.  **Verificar Logs:**
    * Observe o terminal ou abra o arquivo `server_log.txt` para ver o registro de todas as suas requisições.

---

### Informações do Projeto

* **Autor:** Victor Torres
* **Professor:** Ygor Amaral Barbosa Leite de Sena
* **Disciplina:** Redes de Computadores
* **Instituição:** Universidade Federal Rural de Pernambuco (UFRPE) - Unidade Acadêmica de Belo Jardim (UABJ)
