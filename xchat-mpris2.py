import xchat, dbus, os, inspect

__module_name__ = "xchat-mpris2" 
__module_version__ = "0.1"
__module_description__ = "Fetches information from MPRIS2-compliant music players" 

conf_file = 'xchat-mpris-player2.txt'

FILE = inspect.currentframe().f_code.co_filename # I died a bit inside...
DIR  = os.path.dirname(FILE)
CONF = os.path.join(DIR, conf_file)

bus = dbus.SessionBus()

player = None

def isPlayerSpecified():
  if player == None:
    xchat.prnt("No player specified.")
    xchat.prnt("Use /player <player name> to specify a default media player.")
    return False
  else:
    return True

def isConfigured():
  return (os.path.exists(CONF) and open(CONF).read() != '')

def loadConfig():
  global player
  if isConfigured():
    player = open(CONF).read()
    return True
  return False

def saveConfig():
  with open(CONF, 'w') as f:
    f.write(player)

def status(str):
  xchat.prnt("[%s] %s" % (player, str))

# Pass in milliseconds, get (minutes, seconds)
def parseSongPosition(time):
  return getMinutesAndSeconds(time / 1000000)

# Pass in just seconds, get (minutes, seconds)
def getMinutesAndSeconds(seconds):
  return (seconds / 60, seconds % 60)

# Pass in both minutes and seconds
def formatTime(time):
  if time > 0:
    return "%d:%02d" % time
  else:
    return "0:00"

def performAction(action):
  try:
    remote_object = bus.get_object("org.mpris.MediaPlayer2.%s" % (player), "/org/mpris/MediaPlayer2")
    iface = dbus.Interface(remote_object, "org.mpris.MediaPlayer2.Player")
    
    fn = getattr(iface, action)
    if fn:
      return fn()
  except dbus.exceptions.DBusException:
    return False

def getProperty(interface, prop):
  try:
    remote_object = bus.get_object("org.mpris.MediaPlayer2.%s" % (player), "/org/mpris/MediaPlayer2")
    iface = dbus.Interface(remote_object, "org.freedesktop.DBus.Properties")
    
    return iface.Get(interface, prop)
  except dbus.exceptions.DBusException:
    return False

def getSongInfo():
  try:
    remote_object = bus.get_object("org.mpris.MediaPlayer2.%s" % (player), "/org/mpris/MediaPlayer2")
    #iface = dbus.Interface(remote_object, "org.freedesktop.MediaPlayer")
    iface = dbus.Interface(remote_object, "org.freedesktop.DBus.Properties")
    
    #if iface.IsPlaying():
    data = iface.Get("org.mpris.MediaPlayer2.Player", "Metadata")
    title = data["xesam:title"]
    album = data["xesam:album"]
    artist = data["xesam:artist"][0]
    pos = getProperty("org.mpris.MediaPlayer2.Player", "Position")
    pos = formatTime(parseSongPosition(pos))
    length = formatTime(parseSongPosition(data["mpris:length"]))
    
    return (artist, title, album, pos, length)
    #else:
    #  return 0
  except dbus.exceptions.DBusException:
    return (False, False, False, False, False)

def getPlayerVersion():
  try:
    remote_object = bus.get_object("org.mpris.MediaPlayer2.%s" % (player), "/org/mpris/MediaPlayer2")
    iface = dbus.Interface(remote_object, "org.freedesktop.MediaPlayer2")
    version = iface.Identity()
    
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    return "DBus Exception"
  return version

def mprisPlayerVersion(word, word_eol, userdata):
  if isPlayerSpecified():
    xchat.prnt(getPlayerVersion())
  return xchat.EAT_ALL

def mprisNp(word, word_eol, userdata):
  if isPlayerSpecified():
    info = getSongInfo()
    if not info == False:
      xchat.command("ME is listening to %s - %s [%s] [%s/%s]" % info)
    else:
      xchat.prnt("Error in getSongInfo()")
  return xchat.EAT_ALL

def mprisPlayer(word, word_eol, userdata):
  global player
  if len(word) > 1:
    oldplayer = player
    player = word[1]
    if not isPlayerSpecified():
      pass
    elif oldplayer != '' and oldplayer != player:
      xchat.prnt("Media player changed from \"%s\" to \"%s\"" % (oldplayer, player))
    else:
      xchat.prnt("Media player set to \"%s\"" % player)
    saveConfig()
    return xchat.EAT_ALL
  else:
    pass
  xchat.prnt("USAGE: %s <player name>, set default meda player." % word[0])
  return xchat.EAT_ALL

def mprisPlay(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Playing')
      performAction('Play')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

def mprisPause(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Paused')
      performAction('Pause')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

def mprisStop(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Stopped')
      performAction('Stop')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

def mprisPrev(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Playing previous song.')
      performAction('Previous')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL

def mprisNext(word, word_eol, userdata):
  try:
    if isPlayerSpecified():
      status('Playing next song.')
      performAction('Next')
  except dbus.exceptions.DBusException:
    xchat.prnt("DBus Exception")
    pass
  return xchat.EAT_ALL


if isConfigured():
  loadConfig()

xchat.prnt("MPRIS2 now playing script initialized")
xchat.prnt("Use /player <player name> to specify the media player you are using.")
xchat.prnt("Use /np to send information on the current song to the active channel.")
xchat.prnt("Also provides: /next, /prev, /play, /pause, /stop, /playerversion")
xchat.hook_command("PLAYER", mprisPlayer, help="Usage: PLAYER <player name>, set default player.\nOnly needs to be done initially and when changing players.")
xchat.hook_command("NP",     mprisNp,     help="Usage: NP, send information on current song to the active channel")
xchat.hook_command("NEXT",   mprisNext,   help="Usage: NEXT, play next song")
xchat.hook_command("PREV",   mprisPrev,   help="Usage: PREV, play previous song")
xchat.hook_command("PLAY",   mprisPlay,   help="Usage: PLAY, play the music")
xchat.hook_command("PAUSE",  mprisPause,  help="Usage: PAUSE, pause the music")
xchat.hook_command("STOP",   mprisStop,   help="Usage: STOP, hammer time!")
xchat.hook_command("PLAYERVERSION", mprisPlayerVersion, help="Usage: PLAYERVERSION, version of the media player you are using")
