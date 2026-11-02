#!/bin/sh
# Avvisa con una notifica ogni volta che qualcosa finisce negli appunti
# (coexiste con greenclip, che fa la cronologia). Niente contenuto nel
# popup per non esporre password copiate dai password manager.
while clipnotify; do
  notify-send -a clipboard -t 1500 "📋 Copiato negli appunti"
done
