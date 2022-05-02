import pafy
import vlc
import time
import threading
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# No hace falta generar una nueva
DEVELOPER_KEY = 'AIzaSyAQc7OKxUDZIX01RsA4gAU3r4WTPOphSkQ'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Encargado de reproducir audio
class AudioPlayer():
    def __init__(self) -> None:
        self.mutex = threading.Lock()
        self.t = None
        self.player = None
        pass
    
    # Funcion encargada de la reproduccion del audio y de revisar si se ha acabado
    def __playloop(self):
        self.player.play()
        current_state = 1
        while current_state != 6:
            self.mutex.acquire()
            current_state = self.player.get_state()
            self.mutex.release()
            time.sleep(5)
        self.player.stop()
        print("Se acabó")
        # TODO: si hay mas canciones en una cola, seguir reproduciendo
    
    # Pausar la cancion actual
    def pause(self):
        self.mutex.acquire()
        self.player.pause()
        self.mutex.release()
    
    # Parar el reproductor
    def stop(self):
        self.mutex.acquire()
        self.player.stop()
        self.mutex.release()
    
    # Seguir reproduciendo cancion
    def resume(self):
        self.mutex.acquire()
        self.player.play()
        self.mutex.release()
    
    # Obtener Streaming y Crear, a partir de VLC, la reproducción.
    def play(self, source):
        playurl = source.getbest().url
        Instance = vlc.Instance()
        player = Instance.media_player_new()
        Media = Instance.media_new(playurl, ":no-video", ":nooverlay", ":role=music", ":network-caching=5000", ":disk-caching=5000",":file-caching=5000", ":live-caching=100")
        Media.get_mrl()
        player.set_media(Media)
        self.player = player
        self.t = threading.Thread(name='player', target=self.__playloop)
        self.t.daemon = True
        self.t.start()
    
    # Para debuggear, esperar a que el loop de reproduccion acabe
    def wait(self):
        self.t.join()

# Crea objeto con metadatos de video
def pafy_video(video_id):
    url = 'https://www.youtube.com/watch?v={0}'.format(video_id)
    vid = pafy.new(url)
    return vid

# Crear objeto con metadatos de playlist
def pafy_playlist(playlist_id):
    url = "https://www.youtube.com/playlist?list={0}".format(playlist_id)
    playlist = pafy.get_playlist(url)
    return playlist

# Buscar y reproducir en YT
def youtube_search(query, max_res=3):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    # Realizar consulta
    search_response = youtube.search().list(q=query, part='id,snippet', maxResults=max_res).execute()

    # Obtener resultados
    videos = []
    playlists = []
    for search_result in search_response.get('items', []):
        if search_result['id']['kind'] == 'youtube#video':
            videos.append('%s' % (search_result['id']['videoId']))
        elif search_result['id']['kind'] == 'youtube#playlist':
            playlists.append('%s' % (search_result['id']['playlistId']))

    # Obtener primer resultado
    selected = None
    if videos:
        print('Videos:{0}'.format(videos))
        selected = pafy_video(videos[0])
    elif playlists:
        print('Playlists:{0}'.format(playlists))
        pafy_video(playlists[0])
    
    # Si hay video, reproducirlo. Simular una pausa y esperar hasta el final.
    if selected is not None:
        player = AudioPlayer()
        player.play(selected)
        time.sleep(30)
        print("pause")
        player.pause()
        time.sleep(5)
        print("resume")
        player.resume()
        player.wait()
  
def main():
    youtube_search("alright keaton henson")
    pass


if __name__ == "__main__":
    main()