import os
import uuid
import shutil
from flask import Flask, request, render_template, url_for, send_from_directory
from PIL import Image

app = Flask(__name__)

# Usando um diretório local para armazenamento temporário
OUTPUT_FOLDER = "tmp/img_convert"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route("/", methods=["GET", "POST"])
def index():
    imagens_processadas = []
    if request.method == "POST":
        largura = int(request.form.get("largura", 800))
        qualidades_str = request.form.get("qualidades", "10,20,30,40,50,60")
        qualidades = [int(q.strip()) for q in qualidades_str.split(",") if q.strip().isdigit()]
        imagens = request.files.getlist("imagens")

        session_id = str(uuid.uuid4())
        session_folder = os.path.join(OUTPUT_FOLDER, session_id)
        os.makedirs(session_folder, exist_ok=True)

        for imagem in imagens:
            try:
                img = Image.open(imagem)
                nome_base = os.path.splitext(imagem.filename)[0]
                altura = int((img.height * largura) / img.width)
                img_red = img.resize((largura, altura), Image.Resampling.LANCZOS)

                for qualidade in qualidades:
                    nome_saida = f"{nome_base}_q{qualidade}.jpg"
                    caminho_saida = os.path.join(session_folder, nome_saida)
                    img_red.save(caminho_saida, "JPEG", quality=qualidade)

                    imagens_processadas.append({
                        "nome": nome_saida,
                        "url": url_for("get_imagem", session=session_id, filename=nome_saida)
                    })

            except Exception as e:
                print(f"[Erro] {imagem.filename}: {e}")
                continue

        # Gerar o arquivo ZIP - shutil.make_archive cria o arquivo com extensão .zip automaticamente
        zip_file_path = shutil.make_archive(
            os.path.join(OUTPUT_FOLDER, session_id),  # Nome base do arquivo (sem extensão)
            'zip',  # Formato
            session_folder  # Diretório a ser zipado
        )

        # Verificar se o arquivo ZIP foi gerado corretamente
        if not os.path.exists(zip_file_path):
            return f"Erro: Arquivo ZIP não encontrado no caminho {zip_file_path}"

        # Gerar o link para download do arquivo ZIP
        zip_url = url_for("download_zip", session_id=session_id)

        return render_template("resultado.html", imagens=imagens_processadas, zip_url=zip_url)

    return render_template("index.html")


# Rota para servir imagens geradas
@app.route("/static/output/<session>/<filename>")
def get_imagem(session, filename):
    return send_from_directory(os.path.join(OUTPUT_FOLDER, session), filename)


# Rota para fazer o download do arquivo ZIP
@app.route("/download/<session_id>")
def download_zip(session_id):
    # Caminho para o arquivo zip
    zip_file_path = os.path.join(OUTPUT_FOLDER, f"{session_id}.zip")

    # Verifique se o arquivo zip existe
    if not os.path.exists(zip_file_path):
        return f"Erro: Arquivo ZIP não encontrado no caminho {zip_file_path}"

    # Serve o arquivo zip para download
    return send_from_directory(
        OUTPUT_FOLDER,
        f"{session_id}.zip",
        as_attachment=True
    )

# Remova o app.run(), pois o Render usará gunicorn
# Inicia o servidor local
# if __name__ == "__main__":
#    app.run(debug=True)
