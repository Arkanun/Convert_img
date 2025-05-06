import os
import uuid
import shutil
from flask import Flask, request, render_template, url_for, send_from_directory
from PIL import Image

app = Flask(__name__)

# Usando /tmp para armazenamento temporário
OUTPUT_FOLDER = "/tmp/img_convert"
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

        return render_template("resultado.html", imagens=imagens_processadas)

    return render_template("index.html")

# Rota para servir imagens geradas
@app.route("/static/output/<session>/<filename>")
def get_imagem(session, filename):
    # Serve as imagens de dentro do tmp/img_convert/ para download
    return send_from_directory(os.path.join(OUTPUT_FOLDER, session), filename)

@app.route("/download/<session_id>")
def download(session_id):
    # Caminho para a pasta da sessão
    session_folder = os.path.join(OUTPUT_FOLDER, session_id)

    # Cria um arquivo zip da pasta da sessão
    shutil.make_archive(session_folder, 'zip', session_folder)

    # Serve o arquivo zip para download
    return send_from_directory(session_folder, f"{session_id}.zip")

# Remova o app.run(), pois o Render usará gunicorn
# if __name__ == "__main__":
#     app.run(debug=True)
