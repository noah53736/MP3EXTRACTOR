import streamlit as st
import os
import yt_dlp
import requests
import re

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
def search_youtube_with_metadata(metadata):
    """
    Search YouTube using extracted metadata from Spotify/SoundCloud.
    """
    query = f"ytsearch:{metadata}"
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            return info['entries'][0]['webpage_url']
    return None

# ==========================
# Function to Download and Convert
# ==========================
def download_from_link(link):
    """
    Download and convert a video/audio file from a given link (YouTube, SoundCloud, etc.)
    into MP3 format with the highest possible quality.
    """
    output_path = "downloads"
    os.makedirs(output_path, exist_ok=True)  # Create downloads folder if it doesn't exist

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',  # Set to highest quality
        }],
        'windowsfilenames': True  # Ensure filenames are compatible across OS
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info_dict)

            # Adjust for possible extensions (e.g., .webm before .mp3 conversion)
            if not os.path.isfile(filename):
                base, _ = os.path.splitext(filename)
                filename = f"{base}.mp3"

            # Ensure the file exists after potential post-processing
            if not os.path.isfile(filename):
                return None, "Erreur : Fichier téléchargé introuvable après conversion."

            # Convert the downloaded file to bytes for Streamlit preview
            with open(filename, "rb") as f:
                audio_bytes = f.read()

        return audio_bytes, filename
    except Exception as e:
        if "HTTP Error 403" in str(e):
            return None, "Erreur : Accès refusé ou contenu protégé. Vérifiez vos permissions."
        return None, f"Erreur lors du téléchargement : {e}"

# ==========================
# Streamlit App
# ==========================
def main():
    st.title("Téléchargeur universel de contenu (MP3 uniquement)")

    st.write("Entrez un lien provenant de YouTube, SoundCloud, Spotify, ou d'autres plateformes prises en charge.")
    st.write("**Créé par NOAH BEN**")

    # Input for URL
    link = st.text_input("Lien de la vidéo ou audio", "")

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
                youtube_url = search_youtube_with_metadata(metadata)
                if youtube_url:
                    st.info("Correspondance trouvée sur YouTube.")
                    link = youtube_url
                else:
                    st.error("Impossible de trouver une correspondance sur YouTube.")
                    return

            elif platform == "SoundCloud":
                st.info("Lien SoundCloud détecté. Extraction des métadonnées...")
                metadata = get_soundcloud_metadata(link)
                st.write(f"Méta-données trouvées : {metadata}")
                youtube_url = search_youtube_with_metadata(metadata)
                if youtube_url:
                    st.info("Correspondance trouvée sur YouTube.")
                    link = youtube_url
                else:
                    st.error("Impossible de trouver une correspondance sur YouTube.")
                    return

            elif platform == "YouTube":
                st.info("Lien YouTube détecté. Téléchargement en cours...")

            else:
                st.error("Plateforme non prise en charge.")
                return

            with st.spinner("Téléchargement en cours..."):
                audio_bytes, result = download_from_link(link)
                if audio_bytes:
                    st.success("Téléchargement et conversion terminés !")
                    st.audio(audio_bytes, format="audio/mp3")

                    # Button to download the audio file
                    st.download_button(
                        label="Télécharger le fichier MP3",
                        data=audio_bytes,
                        file_name=result.split("/")[-1],
                        mime="audio/mpeg"
                    )
                else:
                    st.error(result)

    # Information section
    st.write("---")
    st.info("Cette application utilise yt-dlp, FFmpeg et une extraction intelligente des métadonnées pour garantir des téléchargements précis. Assurez-vous d'utiliser cette application de manière conforme aux lois sur les droits d'auteur.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
