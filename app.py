import streamlit as st
import os
import yt_dlp
import subprocess

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
# Function to Search YouTube Without API
# ==========================
def search_youtube_without_api(query):
    """
    Use yt-dlp to search for a video on YouTube based on the query.
    Return the URL of the first video found.
    """
    search_url = f"ytsearch:{query}"
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_url, download=False)
        if 'entries' in info and len(info['entries']) > 0:
            return info['entries'][0]['webpage_url']
    return None

# ==========================
# Function to Handle DRM Content
# ==========================
def handle_drm_content(link):
    """
    Attempt to handle DRM-protected content using an external downloader.
    This function assumes StreamFab DRM M3U8 Downloader is installed.
    """
    output_path = "downloads"
    os.makedirs(output_path, exist_ok=True)

    try:
        # Command to invoke StreamFab DRM M3U8 Downloader (example, may vary)
        command = [
            "streamfab", "--url", link, "--output", output_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode == 0:
            # Find the downloaded file in the output directory
            downloaded_files = [f for f in os.listdir(output_path) if f.endswith(('.mp4', '.mkv'))]
            if downloaded_files:
                file_path = os.path.join(output_path, downloaded_files[0])
                with open(file_path, "rb") as f:
                    return f.read(), file_path
            else:
                return None, "Erreur : Aucun fichier téléchargé trouvé."
        else:
            return None, f"Erreur DRM : {result.stderr}"
    except Exception as e:
        return None, f"Erreur lors du traitement DRM : {e}"

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
        if "DRM" in str(e):
            return handle_drm_content(link)
        return None, f"Erreur lors du téléchargement : {e}"

# ==========================
# Streamlit App
# ==========================
def main():
    st.title("Téléchargeur universel de contenu (MP3 uniquement)")

    st.write("Entrez un lien provenant de YouTube, SoundCloud, Spotify, ou d'autres plateformes prises en charge.")

    # Input for URL
    link = st.text_input("Lien de la vidéo ou audio", "")

    # Button to trigger download
    if st.button("Télécharger"):
        if not link:
            st.error("Veuillez entrer un lien valide.")
        else:
            platform = identify_platform(link)

            if platform == "Spotify":
                st.info("Lien Spotify détecté. Recherche sur YouTube...")
                # Example: Hardcoded query for simplicity
                query = "Example song by Example artist"
                youtube_url = search_youtube_without_api(query)
                if youtube_url:
                    link = youtube_url
                else:
                    st.error("Impossible de trouver une correspondance sur YouTube.")
                    return

            elif platform == "SoundCloud":
                st.info("Lien SoundCloud détecté. Traitement en cours...")

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
    st.info("Cette application utilise yt-dlp, FFmpeg et peut gérer certains contenus protégés par DRM via un outil externe. Assurez-vous d'utiliser cette application de manière conforme aux lois sur les droits d'auteur.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
