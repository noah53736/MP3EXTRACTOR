import streamlit as st
import os
import yt_dlp

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

    # yt-dlp options
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
            ydl.download([link])
        return f"Téléchargement terminé. Fichiers disponibles dans le dossier '{output_path}'."
    except Exception as e:
        return f"Erreur lors du téléchargement : {e}"

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
                result = download_from_link(link, output_format=format_choice)
                st.success(result)

    # Information section
    st.write("---")
    st.info("Cette application utilise yt-dlp et FFmpeg pour télécharger et convertir le contenu. Assurez-vous d'utiliser cette application de manière conforme aux lois sur les droits d'auteur.")

# Run the Streamlit app
if __name__ == "__main__":
    main()
