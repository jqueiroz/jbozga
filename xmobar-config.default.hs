Config
    { font = "xft:Bitstream Vera Sans Mono:size=14:bold:antialias=true"
    , borderColor = "black"
    , border = TopB
    , bgColor = "black"
    , fgColor = "grey"
    , position = Bottom
    , allDesktops = True
    , lowerOnStart = False
    , overrideRedirect = True
    , commands = [Run PipeReader "/home/john/.jbozga_pipe" "jbozga"]
    , sepChar = "%"
    , alignSep = "}{"
    , template = "%jbozga%"
    }
