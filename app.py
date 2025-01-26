import streamlit as st
import os
import yt_dlp
from pydub import AudioSegment

# ==========================
# Function to Download and Convert
# ==========================
def download_from_link(link, output_format="mp3"):
    """
    Download and convert a video/audio file from a given link (YouTube, SoundCloud, etc.)
    into the specified output format.
    """
    output_path = "downloads"
    os.makedirs(output_path, exist_ok=True)  # Create downloads folder if it doesn't exist

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': output_format,
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info_dict)

        # Convert the downloaded file to bytes for Streamlit preview
        with open(filename, "rb") as f:
            audio_bytes = f.read()

        return audio_bytes, filename
    except Exception as e:
        return None, f"Erreur lors du téléchargement : {e}"

# ==========================
# Streamlit App
# ==========================
def main():
    st.title("Téléchargeur universel de contenu")

    st.write("Entrez un lien provenant de YouTube, SoundCloud ou d'autres plateformes prises en charge.")

    # Input for URL
    link = st.text_input("Lien de la vidéo ou audio", "")

    # Select format
    format_choice = st.selectbox("Format de sortie", ["mp3", "mp4"])

    # Button to trigger download
    if st.button("Télécharger"):
        if not link:
            st.error("Veuillez entrer un lien valide.")
        else:
            with st.spinner("Téléchargement en cours..."):
                audio_bytes, result = download_from_link(link, output_format=format_choice)
                if audio_bytes:
                    st.success("Téléchargement et conversion terminés !")
                    st.audio(audio_bytes, format="audio/mp3")

                    # Button to download the audio file
                    st.download_button(
                        label="Télécharger le fichier",
                        data=audio_bytes,
                        file_name=result.split("/")[-1],
                        mime="audio/mpeg" if format_choice == "mp3" else "video/mp4"
                    )
                else:
                    st.error(result)

    # Information section
    st.write("---")
    st.info("Cette application utilise yt-dlp et FFmpeg pour télécharger et convertir le contenu. Assurez-vous d'utiliser cette application de manière conforme aux lois sur les droits d'auteur.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
