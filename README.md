1. Projeto Portal do Contador
1.1. Descrição
Este projeto é uma aplicação web desenvolvida em Flask que serve como um portal de arquivos para escritórios de contabilidade. A aplicação permite que contadores façam login e acessem pastas específicas do Google Drive associadas às empresas de seus clientes, de forma segura e organizada.
O sistema possui dois níveis de acesso:
Contador: Pode visualizar as empresas vinculadas a ele e navegar pelas pastas do Drive.
Administrador: Pode cadastrar novos contadores, novas empresas e gerenciar os vínculos entre empresas e pastas do Google Drive.
1.2. Tecnologias Utilizadas
Backend: Python
Framework: Flask
Banco de Dados: SQLite
APIs Externas: Google Drive API (para listagem de arquivos)
Frontend: HTML, CSS (Jinja2 para templates)
Autenticação: Sessões Flask (para login)
2. Como Instalar e Executar o Projeto
Siga os passos abaixo para configurar e executar o ambiente de desenvolvimento local.
2.1. Pré-requisitos
Python 3.10 ou superior
Conta do Google Cloud com a API do Google Drive ativada
2.2. Passos da Instalação
Clonar o Repositório:
git clone [URL_DO_SEU_REPOSITORIO]
cd [NOME_DA_PASTA_DO_PROJETO]


Criar e Ativar o Ambiente Virtual (Venv):
# Criar o ambiente
python -m venv .venv
# Ativar (Linux/macOS)
source .venv/bin/activate
# Ativar (Fish)
source .venv/bin/activate.fish
# Ativar (Windows)
.venv\Scripts\activate


Instalar as Dependências:
pip install -r requirements.txt


Configurar o Ambiente (.env e Credenciais):
Crie um arquivo .env na raiz do projeto e adicione sua SECRET_KEY:
SECRET_KEY='sua-chave-secreta-e-longa-aqui'


Credenciais do Google:
Baixe o arquivo credentials.json do seu projeto no Google Cloud Console.
Coloque este arquivo na raiz do projeto.
Importante: Adicione .env, token.json e credentials.json ao seu arquivo .gitignore para não expor suas chaves!
Inicializar o Banco de Dados:
Execute o script de setup para criar as tabelas no seu banco de dados (ex: usuarios.db).
python setup_database.py


Executar a Aplicação:
flask run --debug
# Ou, se o seu ponto de entrada for app.py:
python app.py


Primeiro Acesso:
Acesse http://127.0.0.1:5000 no seu navegador.
Ao executar uma ação que usa a API do Google pela primeira vez, o navegador abrirá para autorização. Siga os passos para gerar o token.json.
3. Estrutura das Rotas (Endpoints)
/: Redireciona para o login ou dashboard.
/login: Página de login.
/logout: Encerra a sessão do usuário.
/dashboard: Painel principal do contador, onde ele vê empresas e arquivos.
/admin: (Admin) Página para cadastros (Contador, Empresa).
/drive: (Admin) Página para buscar e vincular pastas do Drive.
/salvar-vinculo: (Admin) Ação de salvar o vínculo.
