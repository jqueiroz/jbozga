#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import logging
import traceback
import xml.etree.ElementTree as ET

# TODO: "toljinga" does not work

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("jbozga")
logger.setLevel(logging.INFO)

class Dictionary:
    def __init__(self, jbovlaste_dump_filename):
        self.entries = {}
        self.index_rafsi = {}
        self.index_glossword = {}
        tree = ET.parse(jbovlaste_dump_filename)
        root = tree.getroot()
        for valsi in root.iter("valsi"):
            entry = {}
            entry['word'] = valsi.attrib['word']
            entry['type'] = valsi.attrib['type']
            definition = valsi.find('definition')
            if definition.text is None:
                continue
            entry['definition'] = self.normalize_definition(definition.text)
            selmaho = valsi.find('selmaho')
            if selmaho is not None:
                entry['selmaho'] = selmaho.text
            notes = valsi.find('notes')
            if notes is not None:
                entry['notes'] = notes.text
            for glossword in valsi.findall('glossword'):
                if 'glosswords' not in entry:
                    entry['glosswords'] = []
                entry['glosswords'].append(glossword.attrib['word'])
                normalized_glossword_key = self.normalize_entry_key(glossword.attrib['word'])
                if normalized_glossword_key not in self.index_glossword:
                    self.index_glossword[normalized_glossword_key] = []
                self.index_glossword[normalized_glossword_key].append({'entry': entry, 'sense': glossword.attrib.get('sense', None)})
            for rafsi in valsi.findall('rafsi'):
                rafsi_text = rafsi.text.replace('&apos;', '\'')
                entry['rafsi'] = entry.get('rafsi', [])
                entry['rafsi'].append(rafsi_text)
                self.index_rafsi[rafsi_text] = entry['word']
            self.entries[self.normalize_entry_key(entry['word'])] = entry
    def normalize_entry_key(self, entry_key):
        if entry_key is None:
            return None
        return entry_key.lower().lstrip(".").replace("’", "'")
    def normalize_definition(self, definition):
        new_definition = []
        for (i, part) in enumerate(definition.split("$")):
            if i % 2 == 1:
                for (x, y) in [("1", "₁"), ("2", "₂"), ("3", "₃"), ("4", "₄"), ("5", "₅")]:
                    part = part.replace("_%s" % x, "%s" % y)
                    part = part.replace("_{%s}" % x, "%s" % y)
            new_definition.append(part)
        return "".join(new_definition)
    def lookup(self, word):
        normalized_word = self.normalize_entry_key(word)
        return self.entries.get(normalized_word, None)
    def lookup_by_rafsi(self, rafsi):
        normalized_rafsi = self.normalize_entry_key(rafsi)
        word = self.index_rafsi.get(normalized_rafsi, None)
        if word:
            normalized_word = self.normalize_entry_key(word)
            return self.lookup(normalized_word)
        else:
            return None
    def lookup_all_by_glossword(self, word):
        normalized_word = self.normalize_entry_key(word)
        return self.index_glossword.get(normalized_word, [])
    def lookup_best_by_glossword(self, word):
        results = self.lookup_all_by_glossword(word)
        for result in results:
            if result['sense'] is None:
                return result['entry']
        if results:
            return results[0]['entry']
        else:
            return None

class Runner:
    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.previous_clipboard = ""
        self.previous_response = ""

    def build_response(self, entry):
        definition = entry['definition'].replace("₁", "1").replace("₂", "2").replace("₃", "3").replace("₄", "4").replace("₅", "5")
        return "<fc=#00ffff>%s:</fc> %s" % (entry['word'], definition)

    def retrieve_response(self, clipboard):
        selected_entries = []
        def append_entry(entry):
            if entry is not None:
                selected_entries.append(self.build_response(entry))

        # Look up word
        append_entry(self.dictionary.lookup(clipboard))

        # Look up by rafsi
        append_entry(self.dictionary.lookup_by_rafsi(clipboard))

        # Look up by glossord, as a fallback
        if not selected_entries:
            append_entry(self.dictionary.lookup_best_by_glossword(clipboard))

        # Prepare the final response
        if selected_entries:
            return "     ".join(selected_entries)
        else:
            return None

    def process_next_message(self):
        try:
            # Retrieve clipboard text
            try:
                clipboard = subprocess.check_output(['xclip',  '-o', 'selection', 'clipboard'], timeout=1).decode('utf-8').strip()
            except subprocess.TimeoutExpired:
                logger.warning("Process call to xclip timed out")
                clipboard = ""
            except:
                logger.error("Caught unexpected exception while attempting to read from xclip. Silently ignoring, and pretending that the clipboard is empty/unchanged...\n%s" % traceback.format_exc())
                #return "<fc=#ffff00>(hopefully) transient error</fc>"
                clipboard = ""
            # Return the cached response, if it is still valid
            if clipboard == self.previous_clipboard:
                return self.previous_response
            # Fetch the new response
            response = self.retrieve_response(clipboard)
            if response is not None:
                self.previous_clipboard = clipboard
                self.previous_response = self.retrieve_response(clipboard)
            # Return
            return self.previous_response
        except:
            logger.error("Failed to process message.\n%s" % traceback.format_exc())
            return "<fc=#ff0000>error</fc>"

# TODO: consider automatically downloading the jbovlaste dump, and saving it to $HOME/.jbozga_jbovlaste_dump.xml
def main():
    # Read command line arguments
    if len(sys.argv) not in [2, 3]:
        sys.stderr.write("Error: incorrect number of arguments\n")
        sys.exit(1)

    jbovlaste_dump_filename = sys.argv[1]
    if len(sys.argv) >= 3:
        pipe_filename = sys.argv[2]
    else:
        pipe_filename = os.path.expanduser("~/.jbozga_pipe")
    logger.debug("Fetched command line arguments: (jbovlaste_dump_filename='%s', pipe_filename='%s')" % (jbovlaste_dump_filename, pipe_filename))

    # Initialize dictionary
    jbovlaste_dump_filename = sys.argv[1]
    logger.info("Initializing dictionary with jbovlaste dump from '%s'" % jbovlaste_dump_filename)
    dictionary = Dictionary(jbovlaste_dump_filename)
    logger.debug("Finished initializing the dictionary!")

    # Run
    runner = Runner(dictionary)
    epoch = 0
    success = True
    while True:
        try:
            epoch = epoch + 1
            if epoch != 1:
                logger.info("Waiting before initiating a new epoch...")
                time.sleep(10)
            logger.info("Initiating epoch #%d" % epoch)
            if os.path.isfile(pipe_filename):
                logger.error("The file '%s' already exists, but does not seem to be a pipe. Refusing to run." % pipe_filename)
                success = False
                break
            if not os.path.exists(pipe_filename):
                logger.info("Creating named pipe: '%s'" % pipe_filename)
                os.mkfifo(pipe_filename)
            logger.info("Opening named pipe: '%s'" % pipe_filename)
            with open(pipe_filename, "w") as pipe:
                while True:
                    time.sleep(0.1)
                    pipe.write(runner.process_next_message() + "\n")
                    pipe.flush()
        except KeyboardInterrupt:
            break
        except BrokenPipeError:
            logger.warning("The pipe broke. Retrying soon in a new, and hopefully more prosperous, epoch...")
        except:
            logger.error("Unexpected exception in the main loop.\n%s" % traceback.format_exc())
    if not success:
        sys.exit(2)

if __name__ == "__main__":
    main()
