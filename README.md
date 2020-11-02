# jbozga

A simple statusbar constantly displaying the Lojban definition for the currently selected word (X11 only).

It works as follows:
1. The python script **jbozga-producer.py** constantly inspects the current X11 selection, looks up the dictionary (built from a [jbovlaste](https://jbovlaste.lojban.org/) dump), and whenever an entry is found writes the definition to a named pipe (defaults to "$HOME/.jbozga_pipe").
2. An instance of [xmobar](https://github.com/jaor/xmobar) runs taking input from the named pipe.

## Running manually
You may run this project manually with the following steps:
1. Install xmobar. It is readily available on the built-in package manager from most Linux distributions.
2. Download a jbovlaste dump. For example: `curl "https://raw.githubusercontent.com/jqueiroz/jbovlaste-dumps/master/english/2019-07-06.xml" -o /path/to/jbovlaste.xml`
3. Run the producer script: `./jbozga-producer.py /path/to/jbovlaste.xml`
4. Start xmobar: `xmobar /path/to/xmobar-config.default.hs`

You may want to use your custom xmobar config instead of `xmobar-config.default.hs`.

## Running with nix
Comming soon™

## FAQ
### Why is the font so small/large?
The font size is hardcoded in the default xmonad config. Try changing the "14" on the second line:
`{ font = "xft:Bitstream Vera Sans Mono:size=14:bold:antialias=true"`.
