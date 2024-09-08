from flask import Flask, request, render_template, redirect, url_for
import requests
import os
import yt_dlp
import instaloader
from urllib.parse import urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

WEBHOOK_URL = 'https://discord.com/api/webhooks/1280249315390001152/4ZRlq2yKAmCIvEPSX5d9byjwZUDon9ElMbd4qvi8rAFVGwHnU8Me0MqzUOFa2h_EaZCy'

def download_youtube_video(url):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s',
        'noplaylist': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            info_dict = ydl.extract_info(url, download=False)
            video_title = info_dict.get('title', 'YouTube Video')
            return f"video.{info_dict.get('ext', 'mp4')}", video_title
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar o vídeo do YouTube: {str(e)}")

def download_instagram_video(url):
    L = instaloader.Instaloader()
    try:
        post = instaloader.Post.from_shortcode(L.context, url.split('/')[-2])
        L.download_post(post, target='video')
        for filename in os.listdir('video'):
            if filename.endswith(".mp4"):
                return os.path.join('video', filename), post.title
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar o vídeo do Instagram: {str(e)}")

def download_vimeo_video(url):
    # Implementar o download para Vimeo se necessário
    pass

def download_tiktok_video(url):
    # Implementar o download para TikTok se necessário
    pass

def download_tviplayer_video(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Utilize BeautifulSoup para analisar o HTML e encontrar a URL do vídeo
        soup = BeautifulSoup(response.text, 'html.parser')
        video_tag = soup.find('video')
        
        if video_tag and 'src' in video_tag.attrs:
            video_url = video_tag['src']
            video_response = requests.get(video_url, stream=True)
            video_response.raise_for_status()
            
            with open('video.mp4', 'wb') as f:
                f.write(video_response.content)
                
            return 'video.mp4', 'TVI Player Video'
        else:
            raise RuntimeError("Não foi possível encontrar o vídeo no site.")
    except Exception as e:
        raise RuntimeError(f"Erro ao baixar o vídeo do TVI Player: {str(e)}")

def get_video_source(url):
    parsed_url = urlparse(url)
    if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
        return download_youtube_video
    elif 'instagram.com' in parsed_url.netloc:
        return download_instagram_video
    elif 'vimeo.com' in parsed_url.netloc:
        return download_vimeo_video
    elif 'tiktok.com' in parsed_url.netloc:
        return download_tiktok_video
    elif 'tviplayer.iol.pt' in parsed_url.netloc:
        return download_tviplayer_video
    else:
        raise ValueError("Fonte de vídeo não suportada")
    
    

def send_video_to_webhook(file_path, title):
    with open(file_path, 'rb') as f:
        response = requests.post(
            WEBHOOK_URL, 
            files={'file': (file_path, f, 'video/mp4')},
            data={'content': f"{title}"}
        )
    return response.status_code

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        try:
            download_func = get_video_source(url)
            filepath, title = download_func(url)
            
            status_code = send_video_to_webhook(filepath, title)
            os.remove(filepath)
            
            if status_code == 204:
                message = f"✅ Vídeo '{title}' enviado com sucesso!"
            else:
                message = f"❌ Erro ao enviar o vídeo. Código de status: {status_code}"
            
            # Redirecionar para a página principal com a mensagem como parâmetro de consulta
            return redirect(url_for('index', message=message))
        except Exception as e:
            # Redirecionar para a página principal com a mensagem de erro
            return redirect(url_for('index', message=f"❌ Ocorreu um erro: {str(e)}"))

    # Obter a mensagem da URL de consulta, se existir
    message = request.args.get('message')
    return render_template('index.html', message=message)

if __name__ == "__main__":
    app.run(debug=True)
