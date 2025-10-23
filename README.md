1. Projeto Portal do Contador (Geti Contábil)

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

KEY_FLASK="chave-secreta"
ADMIN_EMAIL="email-do-admin"


Credenciais do Google:

Baixe o arquivo credentials.json do seu projeto no Google Cloud Console.

Coloque este arquivo na raiz do projeto.

Importante: Adicione .env, token.json e credentials.json ao seu arquivo .gitignore para não expor suas chaves!

Inicializar o Banco de Dados:

Execute o script de setup para criar as tabelas no seu banco de dados (ex: usuarios.db).

python init_db.py


Executar a Aplicação:

python app.py


Primeiro Acesso:

Acesse http://127.0.0.1:5000 no seu navegador.

Ao executar uma ação que usa a API do Google pela primeira vez, o navegador abrirá para autorização. Siga os passos para gerar o token.json.

3. Estrutura das Rotas (Endpoints)

/: Redireciona para o login ou dashboard.
/login: Página de login.
/logout: Encerra a sessão do usuário.
/dashboard: Painel principal do contador, onde ele vê empresas e arquivos.
/download/<file_id>: Rota para download de arquivo individual.
/download/batch: Rota para download dos arquivos selecionados em lote (.zip).
/admin: (Admin) Página para cadastros (Contador, Empresa).
/admin/vinculos: (Admin) Página para gerenciar vínculos entre contadores e empresas.
/drive: (Admin) Página para buscar e vincular pastas do Drive.
/salvar_vinculo: (Admin) Ação de salvar o vínculo (empresa <-> drive)

4. Acessos

4.1 Admin:

Credenciais no arquivo .env.
Acesso ao painel administrativo (Botão Admin):

    /admin: Tela de cadstros - O proprio FORMS já informa o que é obrigatório, caso não tenha definida e/ou cadastrado o vinculo relacionado, deixar com a seleção "Admin" para entrada vazia no banco.
    /admin/vinculos: Tela de gerenciamento de vinculos Contador/Empresa - no forms a esquerda pode selecionar a empresa e o contador desejados e usar o botão para Vincular ou Desvincular.
    /drive: Tela de vinculação a pasta no Google Drive - Pesquisar de acordo Nome Fantasia da empresa (Nome dela no Geti Gestor) e selecionar a qual empresa aquela pasta vai pertencer.
    A relação de Empresa X Conador é de N:N (Uma empresa pode ser vinculada a N contadores e N contadores podem ser vinculados a uma mesma empresa).
    O ID do Google Drive é único por empresa, caso seja feita uma vinculação em uma empresa que ja tenha um ID irá retornar um Erro.

O Admin consgue ver o drive de todas as empresas cadastradas, independente de vínculo a contador.

4.2 Contador

Credenciais no banco de dados.
Botão Admin fica oculto e o acesso as paginas pela url retornam na Dashboard.
O contador consegue ter acesso apenas as empresas que foram vinculadas a ele, tendo livre acesso as pastas e arquivos daquela empresa.

5. Funcionalidades

Ao selecionar uma empresa pelo menu lateral, o container principal será atualizado de acordo o ID do Drive vinculado aquela empresa, onde se tem:
    
    Botão Voltar: Caso não esteja na pasta raiz da empresa, o botão retorna para a pasta pai da que esta atualmente.
    Order By: Seleciona a ordenação dos arquivos, por Nome (Ordem Alfabética) ou por Data (Mais recentes primeiro).
    Check Box: A checkbox do cabeçalho seleciona todos os arquivos daquela pasta, as que estão nos arquivos selecionam individualmente.
    Download Individual: Ao clicar no nome do arquivo, será baixado individualmente (mantendo o tipo original .xml, .xlsx, .pdf, etc).
    Download de seleção: Ao selecionar ao menos um arquivo pela checkbox, poderá clicar no botão "Baixar Selecionados" no fim da página para compactar todos os arquivos selecionados e baixar um .zip com eles.