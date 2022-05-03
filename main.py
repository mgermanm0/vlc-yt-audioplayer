from email.mime import audio
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
        self.skip = False
        self.queuemutex = threading.Lock()
        self.queue = []
        pass
    
    def __get_next_song(self):
        try:
            self.queuemutex.acquire()
            if len(self.queue) > 0:
                return self.queue.pop(0)
            return None
        finally:
            self.queuemutex.release()
    def addSource(self, source):
        try:
            self.queuemutex.acquire()
            self.queue.append(source)
            print("Added - ", source.title)
        finally:
            self.queuemutex.release()
    # Funcion encargada de la reproduccion del audio y de revisar si se ha acabado
    def __playloop(self):
        song = self.__get_next_song()
        print(song.title)
        while song != None:
            self.mutex.acquire()
            self.__new_player_media(self.player, song)
            self.player.play()
            self.mutex.release()
            current_state = 1
            while current_state != 6:
                self.mutex.acquire()
                if self.skip:
                    current_state = 6
                    self.skip = False
                    self.player.stop()
                else:
                    current_state = self.player.get_state()
                self.mutex.release()
                time.sleep(5)
            song = self.__get_next_song()
            if song != None:
                print(song.title)
        self.player.stop()

        print("Se acabó")
    
    # Pausar la cancion actual
    def pause(self):
        self.mutex.acquire()
        self.player.pause()
        self.mutex.release()
    
    def next(self):
        self.mutex.acquire()
        self.skip = True
        self.mutex.release()
    # Parar el reproductor
    def stop(self):
        self.queuemutex.acquire()
        self.mutex.acquire()
        self.queue.clear()
        self.player.stop()
        self.queuemutex.release()
        self.mutex.release()
    
    # Seguir reproduciendo cancion
    def resume(self):
        self.mutex.acquire()
        self.player.play()
        self.mutex.release()
    
    
    def __new_player_media(self, player, source):
        playurl = source.getbest().url
        instance = vlc.Instance()
        media = instance.media_new(playurl, ":no-video", ":nooverlay", ":role=music", ":network-caching=5000", ":disk-caching=5000",":file-caching=5000", ":live-caching=100")
        media.get_mrl()
        player.set_media(media)
        
    # Obtener Streaming y Crear, a partir de VLC, la reproducción.
    def play(self, source):
        if self.player is None:
            instance = vlc.Instance()
            player = instance.media_player_new()
            self.addSource(source)
            self.player = player
            self.t = threading.Thread(name='player', target=self.__playloop)
            self.t.daemon = True
            self.t.start()
        else:
            self.addSource(source)
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


def ytsearch(query, max_res=3):
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

    if videos:
        print('Videos:{0}'.format(videos))
    elif playlists:
        print('Playlists:{0}'.format(playlists))
    
    return [pafy_video(x) for x in videos]

# Buscar y reproducir en YT
def youtube_search_play(query, max_res=3, audioplayer=None):
    res = ytsearch(query, max_res)
    # Si hay video, reproducirlo. Simular una pausa y esperar hasta el final.
    if audioplayer is None:
        audioplayer = AudioPlayer()
    audioplayer.play(res[0])
    return audioplayer
  
def main():
    audioplayer=youtube_search_play("Infected Mushroom - Kababies")
    time.sleep(7)
    youtube_search_play("never gonna give you up", audioplayer=audioplayer)
    time.sleep(7)
    youtube_search_play("alright keaton henson", audioplayer=audioplayer)
    time.sleep(30)
    print("pause")
    audioplayer.pause()
    time.sleep(5)
    print("resume")
    audioplayer.resume()
    time.sleep(5)
    print("skip")
    audioplayer.next()
    time.sleep(20)
    audioplayer.next()
    audioplayer.wait()
    pass


if __name__ == "__main__":
    main()