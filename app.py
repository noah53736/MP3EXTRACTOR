import streamlit as st
import os
import yt_dlp
import requests
import re
from PIL import Image
from io import BytesIO

# ==========================
# Function to Identify Platform
# ==========================
def identify_platform(link):
    """
    Identify the platform of the provided link (Spotify, SoundCloud, YouTube, etc.)
    """
    if "spotify.com" in link:
        return "Spotify"
    elif "soundcloud.com" in link:
        return "SoundCloud"
    elif "youtube.com" in link or "youtu.be" in link:
        return "YouTube"
    else:
        return "Unknown"

# ==========================
# Metadata Extraction Functions
# ==========================
def get_spotify_metadata(link):
    """
    Extract metadata (title, artist) from a Spotify track URL.
    """
    try:
        response = requests.get(link)
        if response.status_code == 200:
            title_match = re.search('<title>(.*?)</title>', response.text)
            if title_match:
                title = title_match.group(1).replace(" - Spotify", "").strip()
                return title
        return "Titre inconnu"
    except Exception as e:
        return f"Erreur Spotify : {e}"

def get_soundcloud_metadata(link):
    """
    Extract metadata (title) from a SoundCloud URL.
    """
    try:
        response = requests.get(link)
        if response.status_code == 200:
            title_match = re.search('<title>(.*?)</title>', response.text)
            if title_match:
                title = title_match.group(1).replace(" | Free Listening on SoundCloud", "").strip()
                return title
        return "Titre inconnu"
    except Exception as e:
        return f"Erreur SoundCloud : {e}"

# ==========================
# Function to Search YouTube Without API
# ==========================
def search_youtube_with_metadata(metadata, attempt=1):
    """
    Search YouTube using extracted metadata from Spotify/SoundCloud.
    Retry if the first video is protected or unavailable.
    """
    query = f"ytsearch{attempt}:{metadata}"
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            return info['entries'][0]['webpage_url'], info['entries'][0]['title'], info['entries'][0]['thumbnail']
    return None, None, None

# ==========================
# Function to Download and Retry
# ==========================
def download_with_retry(link, metadata, output_format="mp3", custom_name=None):
    """
    Attempt to download a YouTube video, retrying with alternative links if protected.
    """
    output_path = "downloads"
    os.makedirs(output_path, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, f"%(title)s.%(ext)s" if not custom_name else os.path.join(output_path, f"{custom_name}.%(ext)s")),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': output_format,
            'preferredquality': '320',
        }],
        'windowsfilenames': True
    }

    attempt = 1
    while attempt <= 3:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(link, download=True)
                filename = ydl.prepare_filename(info_dict)

                # Adjust for possible extensions (e.g., .webm before .mp3 conversion)
                if not os.path.isfile(filename):
                    base, _ = os.path.splitext(filename)
                    filename = f"{base}.{output_format}"

                # Ensure the file exists after potential post-processing
                if not os.path.isfile(filename):
                    return None, "Erreur : Fichier téléchargé introuvable après conversion.", link

                # Convert the downloaded file to bytes for Streamlit preview
                with open(filename, "rb") as f:
                    audio_bytes = f.read()

                return audio_bytes, filename, link
        except Exception as e:
            if "HTTP Error 403" in str(e):
                st.warning(f"Lien protégé détecté lors de la tentative {attempt}. Recherche d'un autre lien...")
                link, new_title, _ = search_youtube_with_metadata(metadata, attempt)
                if not link:
                    return None, "Erreur : Aucune correspondance libre trouvée après plusieurs tentatives.", None
                attempt += 1
            else:
                return None, f"Erreur lors du téléchargement : {e}", link

    return None, "Erreur : Téléchargement échoué après plusieurs tentatives.", None

# ==========================
# Streamlit App
# ==========================
def main():
    st.title("Téléchargeur universel de contenu (MP3, WAV, AAC)")

    st.write("Entrez un lien provenant de YouTube, SoundCloud, Spotify, ou d'autres plateformes prises en charge.")
    st.write("**Créé par NOAH BEN**")

    # Input for URL
    link = st.text_input("Lien de la vidéo ou audio", "")

    # Options for format and custom filename
    st.sidebar.header("Options de téléchargement")
    output_format = st.sidebar.selectbox("Format de sortie", ["mp3", "wav", "aac"], index=0)
    custom_name = st.sidebar.text_input("Nom personnalisé du fichier (optionnel)", "")

    # Button to trigger download
    if st.button("Télécharger"):
        if not link:
            st.error("Veuillez entrer un lien valide.")
        else:
            platform = identify_platform(link)

            if platform == "Spotify":
                st.info("Lien Spotify détecté. Extraction des métadonnées...")
                metadata = get_spotify_metadata(link)
                st.write(f"Méta-données trouvées : {metadata}")
                youtube_url, _, thumbnail_url = search_youtube_with_metadata(metadata)
                if youtube_url:
                    st.info("Correspondance trouvée sur YouTube.")
                    link = youtube_url
                    if thumbnail_url:
                        response = requests.get(thumbnail_url)
                        if response.status_code == 200:
                            img = Image.open(BytesIO(response.content))
                            st.image(img, caption="Miniature de la vidéo")
                else:
                    st.error("Impossible de trouver une correspondance sur YouTube.")
                    return

            elif platform == "SoundCloud":
                st.info("Lien SoundCloud détecté. Extraction des métadonnées...")
                metadata = get_soundcloud_metadata(link)
                st.write(f"Méta-données trouvées : {metadata}")
                youtube_url, _, thumbnail_url = search_youtube_with_metadata(metadata)
                if youtube_url:
                    st.info("Correspondance trouvée sur YouTube.")
                    link = youtube_url
                    if thumbnail_url:
                        response = requests.get(thumbnail_url)
                        if response.status_code == 200:
                            img = Image.open(BytesIO(response.content))
                            st.image(img, caption="Miniature de la vidéo")
                else:
                    st.error("Impossible de trouver une correspondance sur YouTube.")
                    return

            elif platform == "YouTube":
                st.info("Lien YouTube détecté. Téléchargement en cours...")
                metadata = ""

            else:
                st.error("Plateforme non prise en charge.")
                return

            with st.spinner("Téléchargement en cours..."):
                audio_bytes, result, final_link = download_with_retry(link, metadata, output_format, custom_name)
                if audio_bytes:
                    st.success("Téléchargement et conversion terminés !")
                    st.audio(audio_bytes, format=f"audio/{output_format}")

                    # Display the final link used
                    st.write(f"[Lien de la vidéo utilisée]({final_link})")

                    # Button to download the audio file
                    st.download_button(
                        label="Télécharger le fichier",
                        data=audio_bytes,
                        file_name=result.split("/")[-1],
                        mime=f"audio/{output_format}"
                    )
                else:
                    st.error(result)

    # Information section
    st.write("---")
    st.info("Cette application utilise yt-dlp, FFmpeg et une extraction intelligente des métadonnées pour garantir des téléchargements précis. Assurez-vous d'utiliser cette application de manière conforme aux lois sur les droits d'auteur.")

# Run the Streamlit app
if __name__ == "__main__":
    main()

